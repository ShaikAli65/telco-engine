from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT / "data" / "Telco-Customer-Churn.csv"
OUTPUT_FILE = ROOT / "data" / "simulated_ticket_logs.json"

TICKET_TYPES = ["complaint", "technical", "billing", "general"]


def load_customers() -> list[dict]:
    if SOURCE_FILE.exists():
        with SOURCE_FILE.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            return list(reader)

    return [
        {
            "customerID": "7590-VHVEG",
            "Contract": "Month-to-Month",
            "Churn": "Yes",
            "MonthlyCharges": "89.85",
        },
        {
            "customerID": "5575-GNVDE",
            "Contract": "One year",
            "Churn": "No",
            "MonthlyCharges": "56.95",
        },
        {
            "customerID": "3668-QPYBK",
            "Contract": "Two year",
            "Churn": "No",
            "MonthlyCharges": "53.85",
        },
    ]


def simulate(customers: list[dict] | None = None) -> list[dict]:
    customers = customers or load_customers()

    now = datetime.now(timezone.utc)
    random.seed(42)
    tickets: list[dict] = []

    for customer in customers[:250]:
        churned = customer.get("Churn") == "Yes"
        contract_type = customer.get("Contract", "Month-to-Month")
        base_count = random.randint(0, 2)
        if contract_type == "Month-to-Month":
            base_count += 1
        if churned:
            base_count += random.randint(2, 5)

        ticket_count = min(base_count, 10)
        for index in range(ticket_count):
            ticket_type = random.choices(
                TICKET_TYPES,
                weights=[0.45, 0.25, 0.2, 0.1] if churned else [0.15, 0.35, 0.25, 0.25],
                k=1,
            )[0]
            sentiment_center = {
                "complaint": -0.8,
                "technical": -0.35,
                "billing": -0.25,
                "general": 0.15,
            }[ticket_type]
            if churned:
                sentiment_center -= 0.1

            tickets.append(
                {
                    "customer_id": customer["customerID"],
                    "ticket_id": f"{customer['customerID']}-T{index + 1}",
                    "ticket_type": ticket_type,
                    "created_at": (
                        now
                        - timedelta(
                            days=random.randint(0, 30 if churned else 120),
                            hours=random.randint(0, 23),
                        )
                    ).isoformat(),
                    "sentiment_score": max(
                        -1.0, min(1.0, round(random.gauss(sentiment_center, 0.18), 3))
                    ),
                }
            )

    return tickets


if __name__ == "__main__":
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(simulate(), indent=2), encoding="utf-8")
    print(f"Wrote simulated ticket logs to {OUTPUT_FILE}")
