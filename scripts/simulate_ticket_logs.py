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


def simulate() -> list[dict]:
    customers: list[dict] = []

    if SOURCE_FILE.exists():
        with SOURCE_FILE.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            customers = list(reader)
    else:
        customers = [
            {"customerID": "7590-VHVEG"},
            {"customerID": "5575-GNVDE"},
            {"customerID": "3668-QPYBK"},
        ]

    now = datetime.now(timezone.utc)
    random.seed(42)
    tickets: list[dict] = []

    for customer in customers[:50]:
        for index in range(random.randint(0, 6)):
            tickets.append(
                {
                    "customer_id": customer["customerID"],
                    "ticket_id": f"{customer['customerID']}-T{index + 1}",
                    "ticket_type": random.choice(TICKET_TYPES),
                    "created_at": (now - timedelta(days=random.randint(0, 45))).isoformat(),
                }
            )

    return tickets


if __name__ == "__main__":
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(simulate(), indent=2), encoding="utf-8")
    print(f"Wrote simulated ticket logs to {OUTPUT_FILE}")

