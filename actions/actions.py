import typing
from typing import Any, Text, Dict, List, Optional, Union
import logging
import os
import pandas as pd

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from .predict import rank_cards
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


        msg = "Here are the cards I recommend:\n"
        recommended_cards_list = []
        events = []

        logger.debug(f"Processing top_cards_df (head(3)): \n{top_cards_df.head(3)}")

        if isinstance(top_cards_df, pd.DataFrame) and 'card_name' in top_cards_df.columns:
            for idx, (_, row) in enumerate(top_cards_df.head(3).iterrows()):
                card_name = row.get('card_name', f'Recommended Card {idx+1}')
                p_approve = row.get('p_approve', None)
                utility = row.get('utility', None)

                approve_text = f"{p_approve:.0%}" if p_approve is not None else "N/A"
                utility_text = f"{utility:.1f}" if utility is not None else "N/A"

                msg += f"- {card_name} (Approval chance: {approve_text}, Utility: {utility_text})\n"
                recommended_cards_list.append(card_name)

                slot_index = idx + 1
                slot_name_to_set = f"recommended_card_{slot_index}"
                logger.debug(f"Preparing to set slot '{slot_name_to_set}' to '{card_name}'")
                events.append(SlotSet(slot_name_to_set, card_name))
        else:
             logger.error(f"Result from rank_cards was not a valid DataFrame or missing 'card_name'. Result: {top_cards_df}")
             dispatcher.utter_message(text="I found some potential matches, but couldn't format the details.")
             return [SlotSet("recommended_cards_list", None), SlotSet("recommended_card_1", None), SlotSet("recommended_card_2", None), SlotSet("recommended_card_3", None)]


        dispatcher.utter_message(text=msg)

        events.append(SlotSet("recommended_cards_list", recommended_cards_list))
        num_recommended = len(recommended_cards_list)
        logger.debug(f"Number recommended = {num_recommended}. Clearing unused slots.")
        if num_recommended < 3:
            logger.debug("Preparing to set recommended_card_3 to None")
            events.append(SlotSet("recommended_card_3", None))
        if num_recommended < 2:
            logger.debug("Preparing to set recommended_card_2 to None")
            events.append(SlotSet("recommended_card_2", None))

        logger.debug(f"ActionRecommendCard returning events: {events}")
        return events

class ActionProvideCardDetails(Action):
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

        if card_name_entity:
             logger.debug(f"Card name entity detected: {card_name_entity}")
             if recommended_list:
                 match = None
                 for rec_name in recommended_list:
                      if rec_name and card_name_entity.lower() == rec_name.lower():
                           match = rec_name
                           logger.debug(f"Exact match found in recommended list: {match}")
                           break
                 if not match:
                      for rec_name in recommended_list:
                           if rec_name and card_name_entity.lower() in rec_name.lower():
                                match = rec_name
                                logger.debug(f"Partial match found in recommended list: {match}")
                                break
                 if match:
                      target_card_name = match
                 else:
                      logger.debug(f"Card entity '{card_name_entity}' not found in recommended list {recommended_list}. Will attempt general lookup.")
                      target_card_name = card_name_entity
             else:
                  logger.debug("No recommended list found in slots, using entity directly.")
                  target_card_name = card_name_entity

        elif ordinal_value:
             logger.debug(f"Ordinal value detected: {ordinal_value}")
             if str(ordinal_value).lower() in ["first", "1st", "initial", "primary", "1"]: target_card_name = card_1
             elif str(ordinal_value).lower() in ["second", "2nd", "2"]: target_card_name = card_2
             elif str(ordinal_value).lower() in ["third", "3rd", "3"]: target_card_name = card_3
             elif str(ordinal_value).lower() in ["last", "final", "ending"] :
                  target_card_name = next((card for card in [card_3, card_2, card_1] if card is not None), None)

             if target_card_name:
                  logger.debug(f"Mapped ordinal '{ordinal_value}' to card: {target_card_name}")
             else:
                  logger.warning(f"Ordinal '{ordinal_value}' requested, but corresponding recommended card slot is empty or mapping failed.")

        else:
            logger.debug("No card_name or ordinal_reference entity detected.")
            dispatcher.utter_message(text="Which card are you asking about? You can say 'the first one', 'the second card', or mention the card name like 'Chase Sapphire'.")
            return []

        card_details_message = None
        if target_card_name:
            logger.debug(f"Looking up details for target card: '{target_card_name}'")
            try:
                if not isinstance(target_card_name, str) or not target_card_name.strip():
                     logger.warning(f"target_card_name is not a valid string: {target_card_name}")
                     raise ValueError("Invalid card name for lookup")

                card_data = cards_df.loc[cards_df['card_name'].str.lower() == target_card_name.lower()]

                if card_data.empty:
                    logger.debug(f"Exact match failed for '{target_card_name}', trying 'contains'.")
                    card_data = cards_df.loc[cards_df['card_name'].str.lower().str.contains(target_card_name.lower(), na=False)]

                if not card_data.empty:
                    card_info = card_data.iloc[0]
                    logger.debug(f"Found card data: {card_info.to_dict()}")

                    display_name = card_info.get('card_name', target_card_name)
                    issuer = card_info.get('issuer', 'N/A')
                    fee = card_info.get('annual_fee', 'N/A')
                    apr_min = card_info.get('apr_min', 'N/A')
                    apr_max = card_info.get('apr_max', 'N/A')
                    min_score = card_info.get('min_credit_score', 'N/A')
                    details = card_info.get('details', 'More details not available.')

                    fee_text = f"${fee:.0f}" if pd.notna(fee) and fee != 0 else ("No Annual Fee" if pd.notna(fee) and fee == 0 else 'N/A')
                    apr_text = f"{apr_min:.1f}% - {apr_max:.1f}%" if pd.notna(apr_min) and pd.notna(apr_max) else ('N/A' if pd.isna(apr_min) and pd.isna(apr_max) else f"{apr_min or apr_max:.1f}%") # Handle single APR value
                    score_text = ""
                    try:
                        score_num = int(float(min_score)) if pd.notna(min_score) else 0
                        if score_num > 0 : score_text = f" (Recommended Score: {score_num}+)"
                    except (ValueError, TypeError):
                         score_text = ""

                    card_details_message = (
                        f"Here are some details for the {display_name} from {issuer}{score_text}:\n"
                        f"- Annual Fee: {fee_text}\n"
                        f"- Purchase APR: {apr_text}\n"
                        f"- Notes: {details}"
                    )
                else:
                    logger.warning(f"Card '{target_card_name}' not found in catalogue after exact and contains check.")
                    card_details_message = f"Sorry, I couldn't find specific details for '{target_card_name}' in my catalogue."

            except KeyError as e:
                 logger.error(f"CSV Column mismatch error when accessing card details: {e}. Check CSV column names used in actions.py matches CSV header.", exc_info=True)
                 card_details_message = f"Sorry, there was an issue retrieving some details for {target_card_name} (data field missing)."
            except Exception as e:
                 logger.error(f"Unexpected error fetching details for {target_card_name}: {e}", exc_info=True)
                 card_details_message = f"Sorry, an unexpected error occurred while fetching details for {target_card_name}."

        else:
            logger.debug("target_card_name is None or empty.")
            if ordinal_value:
                 card_details_message = f"You asked about the {ordinal_value} card, but I don't seem to have recommended that many or the slot was empty. Can you clarify which card?"
            elif not card_details_message:
                 card_details_message = "Sorry, I couldn't determine which card you were asking about."


        if card_details_message:
            dispatcher.utter_message(text=card_details_message)

        return []