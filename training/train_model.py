"""
Retrieves point-in-time training data from Feast’s offline store, then
“trains” a z-score model on it.
The model parameters are written to training/model_params.json so that the
Django view reads them instead of having to copy them in by hand.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from feast import FeatureStore

BASE_DIR = Path(__file__).resolve().parent.parent
TRANSACTIONS_PARQUET_FILE = BASE_DIR / "data" / "transactions.parquet"
PARAMS_PATH = Path(__file__).resolve().parent / "model_params.json"
store = FeatureStore(repo_path=str(BASE_DIR / "feature_repo" / "feature_repo"))
transactions_df = pd.read_parquet(TRANSACTIONS_PARQUET_FILE)


# Extra entity_df columns (here, the is_fraudulent label) are passed through to the result unchanged.
entity_df = transactions_df[["user_id", "event_timestamp", "is_fraudulent"]].copy()
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=[
        "transaction_features:amount",
        "transaction_features:category",
        "transaction_features:location",
    ],
).to_df()
print(training_df.head(10))
print(f"\nPulled {len(training_df)} rows of training data.")

# --- The “model”: mean and standard deviation of log(amount) ---
# Amounts are right-skewed (lognormal), so the z-score is computed on 
# log(amount), which is roughly normal. The baseline is fit on legitimate
# transactions only, so fraud doesn’t inflate its own threshold.
# A transaction is flagged if its log-amount is more than 2 standard
# deviations ABOVE the mean (one-sided: unusually small amounts aren’t flagged).


legit_log_amounts = np.log(training_df.loc[~training_df["is_fraudulent"], "amount"])
TRAIN_MEAN_LOG_AMOUNT = float(legit_log_amounts.mean())
TRAIN_STD_LOG_AMOUNT = float(legit_log_amounts.std())
PARAMS_PATH.write_text(
    json.dumps(
        {
            "mean_log_amount": TRAIN_MEAN_LOG_AMOUNT,
            "std_log_amount": TRAIN_STD_LOG_AMOUNT,
            "z_score_threshold": 2.0,
        },
        indent=2,
    )
    + "\n"
)
print(f"\nFit on {len(legit_log_amounts)} legitimate transactions.")
print("Trained model parameters:")
print(f"TRAIN_MEAN_LOG_AMOUNT = {TRAIN_MEAN_LOG_AMOUNT}")
print(f"TRAIN_STD_LOG_AMOUNT = {TRAIN_STD_LOG_AMOUNT}")
print(f"\nWrote parameters to {PARAMS_PATH}")