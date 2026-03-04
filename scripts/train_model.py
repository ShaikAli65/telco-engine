from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.feature_engineering import (
    CATEGORICAL_FEATURE_COLUMNS,
    MODEL_FEATURE_COLUMNS,
    NUMERIC_FEATURE_COLUMNS,
    build_feature_row,
)
from app.models import ContractType, CustomerProfile, RiskRequest, Ticket, TicketType
from .simulate_ticket_logs import OUTPUT_FILE, SOURCE_FILE, load_customers, simulate


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts"
MODEL_ARTIFACT = ARTIFACT_DIR / "churn_model.joblib"
METRICS_ARTIFACT = ARTIFACT_DIR / "metrics.json"


def _normalize_contract(value: str | None) -> str:
    if value in {"Month-to-Month", "Month-to-month"}:
        return ContractType.month_to_month.value
    if value == "Two year":
        return ContractType.two_year.value
    return ContractType.one_year.value


def load_customer_frame() -> pd.DataFrame:
    if SOURCE_FILE.exists():
        frame = pd.read_csv(SOURCE_FILE)
        frame["MonthlyCharges"] = pd.to_numeric(frame["MonthlyCharges"], errors="coerce").fillna(0.0)
        rng = np.random.default_rng(42)
        delta = rng.normal(
            loc=np.where(frame["Churn"] == "Yes", 9.0, 2.0),
            scale=4.0,
            size=len(frame),
        )
        frame["previous_monthly_charges"] = np.maximum(frame["MonthlyCharges"] - delta, 0.0)
        return frame

    rng = np.random.default_rng(42)
    rows = []
    for index in range(300):
        contract = rng.choice(["Month-to-Month", "One year", "Two year"], p=[0.5, 0.3, 0.2])
        tenure = int(rng.integers(1, 72))
        monthly = round(float(rng.uniform(30, 120)), 2)
        churn_prob = 0.55 if contract == "Month-to-Month" else 0.22
        churn = "Yes" if rng.random() < churn_prob else "No"
        previous = max(0.0, monthly - float(rng.normal(7 if churn == "Yes" else 2, 4)))
        rows.append(
            {
                "customerID": f"SYN-{index:04d}",
                "Contract": contract,
                "MonthlyCharges": monthly,
                "previous_monthly_charges": round(previous, 2),
                "tenure": tenure,
                "Churn": churn,
            }
        )
    return pd.DataFrame(rows)


def load_ticket_frame(customers: list[dict]) -> pd.DataFrame:
    if OUTPUT_FILE.exists():
        return pd.read_json(OUTPUT_FILE)

    tickets = simulate(customers)
    OUTPUT_FILE.write_text(json.dumps(tickets, indent=2), encoding="utf-8")
    return pd.DataFrame(tickets)


def build_training_frame(customer_frame: pd.DataFrame, ticket_frame: pd.DataFrame) -> pd.DataFrame:
    records = []

    for _, row in customer_frame.iterrows():
        customer_id = row["customerID"]
        customer_tickets = ticket_frame[ticket_frame["customer_id"] == customer_id]
        tickets = [
            Ticket(
                ticket_id=str(ticket_row["ticket_id"]),
                ticket_type=TicketType(ticket_row["ticket_type"]),
                created_at=pd.Timestamp(ticket_row["created_at"]).to_pydatetime(),
                sentiment_score=float(ticket_row.get("sentiment_score"))
                if pd.notna(ticket_row.get("sentiment_score"))
                else None,
            )
            for _, ticket_row in customer_tickets.iterrows()
        ]

        payload = RiskRequest(
            customer=CustomerProfile(
                customer_id=customer_id,
                contract_type=ContractType(_normalize_contract(row.get("Contract"))),
                monthly_charges=float(row.get("MonthlyCharges", 0.0)),
                previous_monthly_charges=float(row.get("previous_monthly_charges", 0.0)),
                tenure_months=int(row.get("tenure", 0)),
            ),
            tickets=tickets,
        )

        record = payload.customer.model_dump()
        record.update(
            {
                **build_feature_row(payload),
                "churned": 1 if row.get("Churn") == "Yes" else 0,
            }
        )
        records.append(record)

    return pd.DataFrame(records)


def train() -> tuple[dict, dict]:
    customer_frame = load_customer_frame()
    customers = load_customers() if SOURCE_FILE.exists() else customer_frame.to_dict(orient="records")
    ticket_frame = load_ticket_frame(customers)
    training_frame = build_training_frame(customer_frame, ticket_frame)

    X = training_frame[MODEL_FEATURE_COLUMNS]
    y = training_frame["churned"]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                CATEGORICAL_FEATURE_COLUMNS,
            ),
            (
                "numeric",
                Pipeline([("imputer", SimpleImputer(strategy="median"))]),
                NUMERIC_FEATURE_COLUMNS,
            ),
        ]
    )

    model = Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=250,
                    max_depth=8,
                    min_samples_leaf=4,
                    random_state=42,
                ),
            ),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    metrics = {
        "f1": round(float(f1_score(y_test, predictions)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "average_precision": round(float(average_precision_score(y_test, probabilities)), 4),
        "precision": round(float(precision_score(y_test, predictions)), 4),
        "recall": round(float(recall_score(y_test, predictions)), 4),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
    }

    bundle = {
        "model": model,
        "metrics": metrics,
        "model_version": "telco-churn-rf-v1",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "feature_columns": MODEL_FEATURE_COLUMNS,
    }
    return bundle, metrics


if __name__ == "__main__":
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    bundle, metrics = train()
    joblib.dump(bundle, MODEL_ARTIFACT)
    METRICS_ARTIFACT.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Saved model artifact to {MODEL_ARTIFACT}")
    print(f"Saved metrics to {METRICS_ARTIFACT}")
