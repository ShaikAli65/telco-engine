from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.inference import ModelInferenceResult
from app.main import app
from app.models import RiskCategory


client = TestClient(app)


def test_predict_risk_endpoint_returns_high_risk():
    with patch("app.main.predict_risk_with_model") as mock_predict:
        mock_predict.return_value = ModelInferenceResult(
            risk=RiskCategory.high,
            churn_probability=0.84,
            model_version="test-model-v1",
            reasons=["Predicted churn probability: 84.00%"],
        )
        payload = {
            "customer": {
                "customer_id": "C100",
                "contract_type": "Month-to-Month",
                "monthly_charges": 95.0,
                "previous_monthly_charges": 80.0,
                "tenure_months": 4,
            },
            "tickets": [
                {
                    "ticket_id": "T001",
                    "ticket_type": "complaint",
                    "created_at": "2026-03-01T00:00:00Z",
                    "sentiment_score": -0.9,
                }
            ],
        }

        response = client.post("/predict-risk", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["risk"] == "High"
    assert body["customer_id"] == "C100"
    assert body["model_version"] == "test-model-v1"
    assert body["churn_probability"] == 0.84


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_info_endpoint():
    with patch("app.main.load_model_bundle") as mock_bundle:
        mock_bundle.return_value = {
            "model_version": "test-model-v1",
            "metrics": {"f1": 0.81},
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }
        response = client.get("/model-info")

    assert response.status_code == 200
    assert response.json()["model_version"] == "test-model-v1"
