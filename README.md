# Fraud Detection with Feast + MongoDB

A hands-on example pipeline that combines **Django** + **django-mongodb-backend**, **Feast**, and **MongoDB** to detect potentially fraudulent transactions.

- Transactions are stored in MongoDB through the Django ORM (`transactions` app).
- Feast defines and manages `transaction_features` (`amount`, `category`, `location`), using a local Parquet file as the offline store and **MongoDB as the online store**.
- A simple z-score model (`training/train_model.py`) is trained on historical features pulled from Feast.
- Features are materialized into MongoDB via `feast materialize`, and a Django view (`transactions/views.py`) scores transactions in real time by looking up each user's latest materialized features.

# .env file

```
# Django
# Generate via shell with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DJANGO_SECRET_KEY=your-secret-key-here

# MongoDB
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>
MONGODB_DB_NAME=fraud_detection
```
## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create a .env file with SECRET_KEY, MONGODB_URI, and DB_NAME (see tutorial.md)

# The `feast` CLI reads MONGODB_URI and DB_NAME from the environment.
set -a; source .env; set +a

python data/generate_transactions.py
python manage.py migrate
python manage.py load_transactions

cd feature_repo/feature_repo
feast apply
# The end date must be after the newest event_timestamp in your data.
feast materialize 2020-01-01T00:00:00 2026-09-01T00:00:00
cd ../..

# Writes training/model_params.json, which the scoring view reads.
cd training && python train_model.py && cd ..

python manage.py runserver
```

Then request a fraud score:

```bash
curl http://127.0.0.1:8000/score/2/
```

```json
{
  "user_id": 2,
  "amount": 28.079999923706055,
  "category": "entertainment",
  "location": "London",
  "z_score": -0.476,
  "is_potentially_fraudulent": false
}
```
