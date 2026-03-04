from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import joblib

from app.feature_engineering import build_feature_row, build_feature_frame
from app.models import RiskCategory, RiskRequest


ARTIFACT_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "churn_model.joblib"


@dataclass(frozen=True)
class ModelInferenceResult:
    risk: RiskCategory
    churn_probability: float
    reasons: list[str]
    model_version: str


def _risk_from_probability(probability: float) -> RiskCategory:
    if probability >= 0.75:
        return RiskCategory.high
    if probability >= 0.4:
        return RiskCategory.medium
    return RiskCategory.low


def _build_reason_strings(feature_row: dict[str, float | str], probability: float) -> list[str]:
    reasons: list[str] = [f"Predicted churn probability: {probability:.2%}"]

    if feature_row["ticket_frequency_30d"] >= 3:
        reasons.append(f"Raised {feature_row['ticket_frequency_30d']} tickets in the last 30 days")
    if feature_row["complaint_ticket_count_90d"] >= 1:
        reasons.append("Complaint tickets observed in the last 90 days")
    if feature_row["ticket_sentiment_score"] < -0.4:
        reasons.append("Support sentiment trend is strongly negative")
    if feature_row["monthly_charge_change"] > 0:
        reasons.append(
            f"Monthly charges increased by {feature_row['monthly_charge_change']:.2f}"
        )
    if feature_row["contract_type"] == "Month-to-Month":
        reasons.append("Customer is on a Month-to-Month contract")

    return reasons


@lru_cache(maxsize=1)
def load_model_bundle() -> dict:
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"Model artifact not found at {ARTIFACT_PATH}. Run scripts/train_model.py first."
        )
    return joblib.load(ARTIFACT_PATH)


def predict_risk(payload: RiskRequest) -> ModelInferenceResult:
    bundle = load_model_bundle()
    model = bundle["model"]
    feature_frame = build_feature_frame(payload)
    probability = float(model.predict_proba(feature_frame)[0][1])
    risk = _risk_from_probability(probability)
    feature_row = build_feature_row(payload)

    return ModelInferenceResult(
        risk=risk,
        churn_probability=round(probability, 4),
        reasons=_build_reason_strings(feature_row, probability),
        model_version=bundle.get("model_version", "unknown"),
    )

