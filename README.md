# Fraud Detection with Feast + MongoDB

A hands-on example pipeline that combines **Django** + **django-mongodb-backend**, **Feast**, and **MongoDB** to detect potentially fraudulent transactions.

- Transactions are stored in MongoDB through the Django ORM (`transactions` app).
- Feast defines and manages `transaction_features` (`amount`, `category`, `location`), using a local Parquet file as the offline store and **MongoDB as the online store**.
- A z-score model (`training/train_model.py`) is trained on historical features pulled from Feast.
- Features are materialized into MongoDB via `feast materialize`, and a Django view (`transactions/views.py`) scores transactions in real time by looking up each user's latest materialized features.

## Requirements

- Python 3.12+
- A MongoDB Atlas cluster (or a local Atlas deployment)

## Quickstart

### Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Create a .env file

Generate a secret key with: 

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Create `.env` in the project root and put the variable values in.

```bash
SECRET_KEY='your-secret-key-here'
MONGODB_URI='mongodb+srv://<username>:<password>@<cluster-url>'
DB_NAME='fraud_detection'
```

### Load `.env` into shell

Django will read the .env file but `Feast` reads the environment variables.

```bash
set -a; source .env; set +a
```

### Run the pipeline

```bash
python data/generate_transactions.py
python manage.py migrate
python manage.py load_transactions

cd feature_repo/feature_repo
feast apply
# The end date must be after the newest event_timestamp in your data.
feast materialize 2020-01-01T00:00:00 2026-09-01T00:00:00
cd ../..

# Writes training/model_params.json, which the scoring view reads.
python training/train_model.py

python manage.py runserver
```

### Request a fraud score:

In a second terminal:

```bash
curl http://127.0.0.1:8000/score/2/
```

```json
{
  "user_id": 2,
  "amount": 28.079999923706055,
  "category": "entertainment",
  "location": "London",
  "z_score": -0.506,
  "is_potentially_fraudulent": false
}
```

User 6's latest transaction is the labelled fraud in the seeded data, so it gets flagged:

```bash
curl http://127.0.0.1:8000/score/6/
```

```json
{
  "user_id": 6,
  "amount": 143.04425048828125,
  "category": "utilities",
  "location": "London",
  "z_score": 4.297,
  "is_potentially_fraudulent": true
}
```