from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_predict_risk_endpoint_returns_high_risk():
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
            },
            {
                "ticket_id": "T002",
                "ticket_type": "billing",
                "created_at": "2026-02-25T00:00:00Z",
            },
            {
                "ticket_id": "T003",
                "ticket_type": "technical",
                "created_at": "2026-02-20T00:00:00Z",
            },
        ],
    }

    response = client.post("/predict-risk", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["risk"] == "High"
    assert body["customer_id"] == "C100"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

