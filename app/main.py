import json
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from app.inference import load_model_bundle, predict_risk as predict_risk_with_model
from app.models import RiskRequest, RiskResponse
from app.observability import RISK_PREDICTIONS, metrics_endpoint, metrics_middleware


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger("telco-rule-engine")

app = FastAPI(
    title="Telco ML Churn Risk Engine",
    description="ML-backed telecom churn risk scoring service using customer and ticket behavior signals.",
    version="2.0.0",
)
app.middleware("http")(metrics_middleware)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", tags=["monitoring"])
async def metrics():
    return await metrics_endpoint()


@app.get("/model-info", tags=["model"])
async def model_info() -> dict:
    try:
        bundle = load_model_bundle()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {
        "model_version": bundle.get("model_version", "unknown"),
        "metrics": bundle.get("metrics", {}),
        "trained_at": bundle.get("trained_at"),
    }


@app.post("/predict-risk", response_model=RiskResponse, tags=["risk"])
async def predict_risk(payload: RiskRequest) -> RiskResponse:
    try:
        result = predict_risk_with_model(payload)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    evaluated_at = datetime.now(timezone.utc)

    logger.info(
        json.dumps(
            {
                "event": "risk_prediction",
                "customer_id": payload.customer.customer_id,
                "risk": result.risk.value,
                "churn_probability": result.churn_probability,
                "model_version": result.model_version,
                "reasons": result.reasons,
                "ticket_count": len(payload.tickets),
                "evaluated_at": evaluated_at.isoformat(),
            }
        )
    )
    RISK_PREDICTIONS.labels(risk=result.risk.value).inc()

    return RiskResponse(
        customer_id=payload.customer.customer_id,
        risk=result.risk,
        churn_probability=result.churn_probability,
        model_version=result.model_version,
        reasons=result.reasons,
        evaluated_at=evaluated_at,
    )
