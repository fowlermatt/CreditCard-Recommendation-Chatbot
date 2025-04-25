# actions/predict.py

import joblib
import pandas as pd
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

ACTIONS_DIR = Path(__file__).parent
PROJECT_DIR = ACTIONS_DIR.parent
MODELDIR = PROJECT_DIR / "ml_models"
DATADIR = PROJECT_DIR / "data"

try:
    clf_path = MODELDIR / "eligibility_clf.pkl"
    clf = joblib.load(clf_path)
    logger.info(f"Successfully loaded model from {clf_path}")
except FileNotFoundError:
    logger.error(f"Model file not found at {clf_path}. Ranking will likely fail.")
    clf = None 
except Exception as e:
    logger.error(f"Error loading model from {clf_path}: {e}", exc_info=True)
    clf = None

try:
    schema_path = MODELDIR / "schema.json"
    with open(schema_path, 'r') as f:
        INPUT_COLS = json.load(f)["input_cols"]
    logger.info(f"Successfully loaded schema from {schema_path}")
except FileNotFoundError:
    logger.error(f"Schema file not found at {schema_path}. Using default or empty columns.")
    INPUT_COLS = []
except Exception as e:
    logger.error(f"Error loading schema from {schema_path}: {e}", exc_info=True)
    INPUT_COLS = []

try:
    csv_path = DATADIR / "cards_catalogue.csv"
    cards = pd.read_csv(csv_path)
    logger.info(f"Successfully loaded card catalogue from {csv_path}")
    if cards.empty:
        logger.warning(f"Card catalogue loaded from {csv_path} is empty.")
except FileNotFoundError:
    logger.error(f"Card catalogue file not found at {csv_path}. Ranking/details will likely fail.")
    cards = pd.DataFrame()
except Exception as e:
    logger.error(f"Error loading card catalogue from {csv_path}: {e}", exc_info=True)
    cards = pd.DataFrame()

def rank_cards(user_dict, top_n: int = 3) -> pd.DataFrame:
    """
    user_dict: mapping of INPUT_COLS → numeric values
    Returns top_n cards sorted by utility = p_approve*rewards_score - annual_fee/100.
    """
    if clf is None:
        logger.error("Eligibility model (clf) not loaded. Cannot predict probabilities.")
        return pd.DataFrame()
    if not INPUT_COLS:
        logger.error("Input columns schema not loaded. Cannot create user DataFrame.")
        return pd.DataFrame()
    if cards.empty:
        logger.error("Card catalogue not loaded or empty. Cannot rank cards.")
        return pd.DataFrame()

    missing_cols = [col for col in INPUT_COLS if col not in user_dict]
    if missing_cols:
        logger.error(f"User dictionary missing required columns: {missing_cols}")
        return pd.DataFrame()

    try:
        user_df = pd.DataFrame([user_dict], columns=INPUT_COLS)

        p = clf.predict_proba(user_df.values)[0, 1]
        logger.debug(f"Predicted probability for eligibility: {p}")

        if not all(col in cards.columns for col in ['min_credit_score', 'min_income']):
             logger.error("Missing 'min_credit_score' or 'min_income' in cards_catalogue.csv")
             return pd.DataFrame()

        eligible = cards[
            (user_dict["fico_high"] >= cards["min_credit_score"]) &
            (user_dict["annual_inc"]  >= cards["min_income"])
        ].copy()

        logger.debug(f"Found {len(eligible)} potentially eligible cards.")
        

        if eligible.empty:
            logger.warning("No cards found meeting minimum score/income requirements.")
            return pd.DataFrame()

        if not all(col in eligible.columns for col in ['rewards_score', 'annual_fee']):
             logger.error("Missing 'rewards_score' or 'annual_fee' in cards_catalogue.csv for eligible cards")
             return pd.DataFrame()

        eligible["p_approve"] = p
        eligible["utility"]   = eligible["p_approve"] * eligible["rewards_score"] - eligible["annual_fee"]/100

        return eligible.sort_values("utility", ascending=False).head(top_n)

    except Exception as e:
        logger.error(f"Error during ranking process: {e}", exc_info=True)
        return pd.DataFrame()