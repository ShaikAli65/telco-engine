import json
import logging
from datetime import datetime, timezone

from fastapi import FastAPI

from app.models import RiskRequest, RiskResponse
from app.observability import RISK_PREDICTIONS, metrics_endpoint, metrics_middleware
from app.rules import evaluate_risk


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger("telco-rule-engine")

app = FastAPI(
    title="Telco Rule-Based Churn Risk Engine",
    description="Rule-based telecom churn risk scoring service with ticket-behavior signals.",
    version="1.0.0",
)
app.middleware("http")(metrics_middleware)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", tags=["monitoring"])
async def metrics():
    return await metrics_endpoint()


@app.post("/predict-risk", response_model=RiskResponse, tags=["risk"])
async def predict_risk(payload: RiskRequest) -> RiskResponse:
    result = evaluate_risk(payload)
    evaluated_at = datetime.now(timezone.utc)

    logger.info(
        json.dumps(
            {
                "event": "risk_prediction",
                "customer_id": payload.customer.customer_id,
                "risk": result.risk.value,
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
        reasons=result.reasons,
        evaluated_at=evaluated_at,
    )

