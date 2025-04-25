import typing
from typing import Any, Text, Dict, List, Optional, Union
import logging
import os
import pandas as pd

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from .predict import rank_cards
from thefuzz import process, fuzz

logger = logging.getLogger(__name__)

ACTIONS_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.dirname(ACTIONS_DIR)
CSV_FILE_PATH = os.path.join(PROJECT_DIR, 'data', 'cards_catalogue.csv')


class ActionRecommendCard(Action):
    def name(self) -> Text:
        return "action_recommend_card"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_dict = {}
        required_slots = ["annual_inc", "fico_high", "dti", "emp_length_num"]
        all_slots_filled = True
        for slot_name in required_slots:
             slot_value = tracker.get_slot(slot_name)
             if slot_value is None or (isinstance(slot_value, str) and not slot_value.strip()):
                 logger.error(f"Slot '{slot_name}' is missing before calling action_recommend_card.")
                 all_slots_filled = False
                 dispatcher.utter_message(text=f"I seem to be missing the required information for '{slot_name}'. Could you please start over?")
                 return []
             try:
                 user_dict[slot_name] = float(slot_value)
             except (ValueError, TypeError):
                 logger.error(f"Could not convert slot '{slot_name}' value '{slot_value}' to float.")
                 dispatcher.utter_message(text=f"There was an issue processing the value provided for {slot_name}.")
                 return []

        if not all_slots_filled or len(user_dict) != len(required_slots):
             logger.error(f"One or more required slots missing or failed conversion. User dict: {user_dict}")
             dispatcher.utter_message(text="I'm still missing some information needed for the recommendation.")
             return []

        logger.debug("Adding missing indicator features (inc_missing, fico_missing) as 0.0")
        user_dict["inc_missing"] = 0.0
        user_dict["fico_missing"] = 0.0

        try:
            logger.debug(f"Calling rank_cards with user_dict: {user_dict}")
            top_cards_df = rank_cards(user_dict, top_n=3)
            if not isinstance(top_cards_df, pd.DataFrame) or top_cards_df.empty:
                 logger.warning(f"rank_cards returned empty or non-DataFrame result for user_dict: {user_dict}")
                 dispatcher.utter_message(text="Sorry, I couldn't find any specific card recommendations based on the provided information.")
                 return [SlotSet("recommended_cards_list", None), SlotSet("recommended_card_1", None), SlotSet("recommended_card_2", None), SlotSet("recommended_card_3", None)]
        except Exception as e:
            logger.error(f"Error calling rank_cards: {e}", exc_info=True)
            dispatcher.utter_message(text="Sorry, an error occurred while trying to find card recommendations.")
            return [SlotSet("recommended_cards_list", None), SlotSet("recommended_card_1", None), SlotSet("recommended_card_2", None), SlotSet("recommended_card_3", None)]


        msg = "Based on your information, here are the cards I recommend:\n"
        recommended_cards_list = []
        events = []

        logger.debug(f"Processing top_cards_df (head(3)): \n{top_cards_df.head(3)}")

        required_output_cols = ['card_name']
        if not all(col in top_cards_df.columns for col in required_output_cols):
             logger.error(f"Result from rank_cards missing required columns. Has: {top_cards_df.columns}. Needs: {required_output_cols}")
             dispatcher.utter_message(text="I found some potential matches, but couldn't get all the details.")
             return [SlotSet(f"recommended_card_{i+1}", None) for i in range(3)] + [SlotSet("recommended_cards_list", None)]

        for idx, (_, row) in enumerate(top_cards_df.head(3).iterrows()):
            card_name = row.get('card_name', f'Recommended Card {idx+1}')
            p_approve = row.get('p_approve', None)
            utility = row.get('utility', None)

            approve_text = f"{p_approve:.0%}" if pd.notna(p_approve) else None
            utility_text = f"{utility:.1f}" if pd.notna(utility) else None

            msg += f"- {card_name}"
            details_list = []
            if approve_text: details_list.append(f"Approval chance: {approve_text}")
            if utility_text: details_list.append(f"Utility: {utility_text}")
            if details_list: msg += f" ({', '.join(details_list)})"
            msg += "\n"

            recommended_cards_list.append(card_name)
            slot_index = idx + 1
            slot_name_to_set = f"recommended_card_{slot_index}"
            logger.debug(f"Preparing to set slot '{slot_name_to_set}' to '{card_name}'")
            events.append(SlotSet(slot_name_to_set, card_name))

        dispatcher.utter_message(text=msg)

        events.append(SlotSet("recommended_cards_list", recommended_cards_list))
        num_recommended = len(recommended_cards_list)
        logger.debug(f"Number recommended = {num_recommended}. Clearing unused slots.")
        for i in range(num_recommended, 3):
            slot_name_to_clear = f"recommended_card_{i+1}"
            logger.debug(f"Preparing to set slot '{slot_name_to_clear}' to None")
            events.append(SlotSet(slot_name_to_clear, None))


        logger.debug(f"ActionRecommendCard returning events: {events}")
        return events

class ActionProvideCardDetails(Action):

    def get_column_for_feature(self, feature_entity: Optional[str]) -> Optional[str]:
        if not feature_entity:
            return None

        feature = feature_entity.lower().strip()

        mapping = {
            "signup bonus": "signup_bonus_details",
            "welcome offer": "signup_bonus_details",
            "bonus": "signup_bonus_details",
            "rewards": "rewards_details",
            "reward details": "rewards_details",
            "points system": "rewards_type",
            "reward type": "rewards_type",
            "cashback": "rewards_details",
            "miles": "rewards_details",
            "points": "rewards_details",
            "foreign transaction fee": "foreign_transaction_fee",
            "ftf": "foreign_transaction_fee",
            "international fee": "foreign_transaction_fee",
            "travel insurance": "travel_insurance_details",
            "trip insurance": "travel_insurance_details",
            "travel protection": "travel_insurance_details",
            "travel perks": "travel_insurance_details",
            "intro apr": "intro_apr_purchase_details",
            "introductory apr": "intro_apr_purchase_details",
            "purchase apr offer": "intro_apr_purchase_details",
            "intro apr purchase": "intro_apr_purchase_details",
            "intro apr bt": "intro_apr_bt_details",
            "balance transfer offer": "intro_apr_bt_details",
            "intro balance transfer": "intro_apr_bt_details",
            "application link": "application_link_placeholder",
            "how to apply": "application_link_placeholder",
            "apply": "application_link_placeholder",
            "annual fee": "annual_fee",
            "fee": "annual_fee",
            "cost": "annual_fee",
            "apr": "apr_min",
            "interest rate": "apr_min",
            "minimum credit score": "min_credit_score",
            "credit score": "min_credit_score",
            "score needed": "min_credit_score",
            "fico": "min_credit_score",
            "issuer": "issuer",
            "who issues": "issuer",
            "bank": "issuer",
            "cell phone protection": "travel_insurance_details",
            "phone insurance": "travel_insurance_details"
        }

        mapping_keys = list(mapping.keys())
        threshold = 80
        best_match, score = process.extractOne(feature, mapping_keys, scorer=fuzz.token_sort_ratio)

        if score >= threshold:
            logger.debug(f"Fuzzy matched feature '{feature}' to mapping key '{best_match}' with score {score}")
            return mapping[best_match]
        else:
            logger.warning(f"Could not confidently fuzzy match feature '{feature}'. Best guess '{best_match}' score {score} < {threshold}.")
            return None

    def name(self) -> Text:
        return "action_provide_card_details"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        try:
            if not os.path.exists(CSV_FILE_PATH):
                logger.error(f"Card catalogue file not found at: {CSV_FILE_PATH}")
                dispatcher.utter_message(text="Sorry, I'm having trouble accessing card details right now (file not found).")
                return []
            cards_df = pd.read_csv(CSV_FILE_PATH)
            cards_df.columns = cards_df.columns.str.strip()
            if cards_df.empty:
                logger.error(f"Card catalogue file is empty: {CSV_FILE_PATH}")
                dispatcher.utter_message(text="Sorry, the card catalogue seems to be empty.")
                return []
        except Exception as e:
             logger.error(f"Failed to load or read card catalogue {CSV_FILE_PATH}: {e}", exc_info=True)
             dispatcher.utter_message(text="Sorry, I encountered an error trying to access card details.")
             return []

        card_name_entity = next(tracker.get_latest_entity_values("card_name"), None)
        ordinal_entity_details = tracker.latest_message.get('entities', [])
        ordinal_value = None
        for entity in ordinal_entity_details:
             if entity.get("entity") == "ordinal_reference":
                  ordinal_value = entity.get('value', entity.get('text'))
                  logger.debug(f"Found ordinal entity: {entity}, using value: {ordinal_value}")
                  break

        recommended_list = tracker.get_slot("recommended_cards_list")
        card_1 = tracker.get_slot("recommended_card_1")
        card_2 = tracker.get_slot("recommended_card_2")
        card_3 = tracker.get_slot("recommended_card_3")
        logger.debug(f"Slots: card_1='{card_1}', card_2='{card_2}', card_3='{card_3}', list='{recommended_list}'")

        target_card_name = None
        card_source = "entity"

        if card_name_entity:
            logger.debug(f"Card name entity detected: {card_name_entity}")
            target_card_name = card_name_entity
            if recommended_list:
                exact_match = next((name for name in recommended_list if name and card_name_entity.lower() == name.lower()), None)
                if exact_match:
                    target_card_name = exact_match
                    card_source = "recommended_list_exact"
                    logger.debug(f"Exact match found in recommended list: {target_card_name}")
                else:
                    partial_match = next((name for name in recommended_list if name and card_name_entity.lower() in name.lower()), None)
                    if partial_match:
                        target_card_name = partial_match
                        card_source = "recommended_list_partial"
                        logger.debug(f"Partial match found in recommended list: {target_card_name}")
                    else:
                         logger.debug(f"Card entity '{card_name_entity}' not found in recommended list {recommended_list}. Will attempt general lookup.")
                         card_source = "entity_general_lookup"

        elif ordinal_value:
            logger.debug(f"Ordinal value detected: {ordinal_value}")
            ord_val_lower = str(ordinal_value).lower()
            if ord_val_lower in ["first", "1st", "initial", "primary", "1"]: target_card_name = card_1
            elif ord_val_lower in ["second", "2nd", "2"]: target_card_name = card_2
            elif ord_val_lower in ["third", "3rd", "3"]: target_card_name = card_3
            elif ord_val_lower in ["last", "final", "ending"]:
                 target_card_name = next((card for card in [card_3, card_2, card_1] if card), None)

            if target_card_name:
                 logger.debug(f"Mapped ordinal '{ordinal_value}' to card from slot: {target_card_name}")
                 card_source = "ordinal"
            else:
                 logger.warning(f"Ordinal '{ordinal_value}' requested, but corresponding recommended card slot is empty or mapping failed.")
                 dispatcher.utter_message(text=f"You asked about the {ordinal_value} card, but I don't have it in the recommendations. Could you specify the name?")
                 return []
        else:
            logger.debug("No card_name or ordinal_reference entity detected.")
            dispatcher.utter_message(text="Which card are you asking about? You can say 'the first one', 'the second card', or mention the card name like 'Chase Sapphire'.")
            return []

        feature_entity = next(tracker.get_latest_entity_values("card_feature"), None)
        logger.debug(f"Detected card_feature entity: {feature_entity}")

        card_details_message = None
        if target_card_name:
            logger.debug(f"Looking up details for target card: '{target_card_name}' (Source: {card_source})")
            try:
                if not isinstance(target_card_name, str) or not target_card_name.strip():
                    logger.warning(f"target_card_name is not a valid string: {target_card_name}")
                    raise ValueError("Invalid card name for lookup")

                card_data = cards_df[cards_df['card_name'].str.lower() == target_card_name.lower()]
                if card_data.empty:
                    logger.debug(f"Exact match failed for '{target_card_name}', trying 'contains'.")
                    card_data = cards_df[cards_df['card_name'].str.lower().str.contains(target_card_name.lower(), na=False)]
                    if len(card_data) > 1:
                        logger.warning(f"'Contains' match for '{target_card_name}' resulted in multiple cards: {card_data['card_name'].tolist()}. Using the first one.")

                if not card_data.empty:
                    card_info = card_data.iloc[0]
                    display_name = card_info.get('card_name', target_card_name)
                    logger.debug(f"Found card data for '{display_name}': {card_info.to_dict()}")

                    if feature_entity:
                        column_name = self.get_column_for_feature(feature_entity)
                        logger.debug(f"Mapped feature '{feature_entity}' to column '{column_name}' using fuzzy matching")

                        if column_name and column_name in card_info and pd.notna(card_info[column_name]):
                            feature_value = card_info[column_name]

                            if column_name == 'annual_fee':
                                fee_text = f"${feature_value:.0f}" if feature_value != 0 else "No Annual Fee"
                                card_details_message = f"The annual fee for the {display_name} is: {fee_text}."
                            elif column_name in ['apr_min', 'apr_max']:
                                apr_min_val = card_info.get('apr_min', None)
                                apr_max_val = card_info.get('apr_max', None)
                                if pd.notna(apr_min_val) and pd.notna(apr_max_val) and apr_min_val != apr_max_val:
                                     apr_text = f"{apr_min_val:.1f}% - {apr_max_val:.1f}%"
                                elif pd.notna(apr_min_val) or pd.notna(apr_max_val):
                                     apr_text = f"{apr_min_val or apr_max_val:.1f}%"
                                else:
                                     apr_text = "Not Available"
                                card_details_message = f"The Purchase APR for the {display_name} is: {apr_text}."
                            elif column_name == 'min_credit_score':
                                score_text = f"{int(float(feature_value))}+" if feature_value > 0 else "No minimum specified (may be for building credit)"
                                card_details_message = f"The recommended minimum credit score for the {display_name} is typically {score_text}."
                            elif column_name == 'foreign_transaction_fee':
                                ftf_text = f"{feature_value}%" if pd.notna(feature_value) and feature_value > 0 else ("No Foreign Transaction Fee" if pd.notna(feature_value) and feature_value == 0 else "Not specified")
                                card_details_message = f"For the {display_name}, the Foreign Transaction Fee is: {ftf_text}."
                            else:
                                card_details_message = f"Regarding the {feature_entity} for the {display_name}: {feature_value}"

                        elif column_name:
                            card_details_message = f"I don't have specific details readily available for '{feature_entity}' for the {display_name}."
                            logger.warning(f"Column '{column_name}' requested but value is NA for card '{display_name}'.")

                        else:
                            card_details_message = f"Sorry, I'm not sure how to look up '{feature_entity}'. I can tell you about things like APR, annual fee, rewards, signup bonus, or travel insurance."

                    else:
                        issuer = card_info.get('issuer', 'N/A')
                        fee = card_info.get('annual_fee', 'N/A')
                        apr_min = card_info.get('apr_min', 'N/A')
                        apr_max = card_info.get('apr_max', 'N/A')
                        min_score = card_info.get('min_credit_score', 'N/A')
                        rewards_summary = card_info.get('rewards_details', None)

                        fee_text = f"${fee:.0f}" if pd.notna(fee) and fee != 0 else ("No Annual Fee" if pd.notna(fee) and fee == 0 else 'N/A')
                        apr_text = f"{apr_min:.1f}% - {apr_max:.1f}%" if pd.notna(apr_min) and pd.notna(apr_max) and apr_min != apr_max else ('N/A' if pd.isna(apr_min) and pd.isna(apr_max) else f"{apr_min or apr_max:.1f}%")
                        score_text = ""
                        try:
                            score_num = int(float(min_score)) if pd.notna(min_score) else 0
                            if score_num > 0: score_text = f" (Recommended Score: {score_num}+)"
                        except (ValueError, TypeError): score_text = ""

                        card_details_message = (
                            f"Okay, here's a general overview of the {display_name} from {issuer}{score_text}:\n"
                            f"- Annual Fee: {fee_text}\n"
                            f"- Purchase APR: {apr_text}"
                        )
                        if pd.notna(rewards_summary):
                             card_details_message += f"\n- Key Feature: {rewards_summary}"

                else:
                    logger.warning(f"Card '{target_card_name}' not found in catalogue after exact and contains check.")
                    if card_source.startswith("recommended_list"):
                         card_details_message = f"Sorry, I recommended '{target_card_name}' but couldn't find its details in my catalogue. There might be an inconsistency."
                    else:
                         card_details_message = f"Sorry, I couldn't find specific details for a card named '{target_card_name}' in my catalogue."

            except KeyError as e:
                 logger.error(f"CSV Column mismatch error: {e}. Check CSV header and column names used in actions.py.", exc_info=True)
                 card_details_message = f"Sorry, there's an issue with my data configuration for {target_card_name} (missing expected data field: {e})."
            except Exception as e:
                 logger.error(f"Unexpected error fetching details for {target_card_name}: {e}", exc_info=True)
                 card_details_message = f"Sorry, an unexpected error occurred while fetching details for {target_card_name}."

        else:
            logger.debug("target_card_name could not be determined.")
            if not card_details_message:
                card_details_message = "Sorry, I couldn't determine which card you were asking about."


        if card_details_message:
            dispatcher.utter_message(text=card_details_message)
        else:
             logger.error("No card_details_message was generated in action_provide_card_details")
             dispatcher.utter_message(text="Sorry, I couldn't process that request.")

        return []