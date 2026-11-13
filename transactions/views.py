import json
import math

from django.conf import settings
from django.http import JsonResponse

from transactions.feast_client import get_latest_transaction_features

PARAMS_PATH = settings.BASE_DIR / "training" / "model_params.json"
def _load_model_params():
    with open(PARAMS_PATH) as f:
        return json.load(f)
    

def score_transaction(request, user_id: int):
    try:
        params = _load_model_params()
    except FileNotFoundError:
        return JsonResponse(
            {"error": "Model parameters not found. Run training/train_model.py first."},
            status=503,
        )
    

    features = get_latest_transaction_features(user_id)
    amount = features.get("amount")
    if amount is None:
        return JsonResponse(
            {"error": f"No features found for user_id {user_id}"}, status=404
        )
    

    # The model works on log(amount) so only unusually LARGE amounts are flagged.
    z_score = (math.log(amount) - params["mean_log_amount"]) / params["std_log_amount"]
    is_potentially_fraudulent = z_score > params["z_score_threshold"]
    return JsonResponse({
        "user_id": user_id,
        "amount": amount,
        "category": features.get("category"),
        "location": features.get("location"),
        "z_score": round(z_score, 3),
        "is_potentially_fraudulent": is_potentially_fraudulent,
    })