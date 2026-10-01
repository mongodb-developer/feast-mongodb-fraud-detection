from decimal import Decimal

import pandas as pd
from django.core.management.base import BaseCommand
from transactions.models import Transaction

class Command(BaseCommand):
    help = "Loading transaction data from data/transactions.parquet into the database via Django ORM"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="data/transactions.parquet",
            help="Path to the Parquet file containing transaction data",
        )

    def handle(self, *args, **options):
        df = pd.read_parquet(options["path"])
        transactions = [
            Transaction(
                 user_id=int(row["user_id"]),
                transaction_id=row["transaction_id"],
                amount=Decimal(f"{row['amount']:.2f}"),
                category=row["category"],
                location=row["location"],
                timestamp=row["event_timestamp"],
            )
            for row in df.to_dict("records")
        ]

        Transaction.objects.all().delete()
        Transaction.objects.bulk_create(transactions)

        self.stdout.write(
            self.style.SUCCESS(
                f" Loaded {len(transactions)} transactions into MDB database."
            )
        )