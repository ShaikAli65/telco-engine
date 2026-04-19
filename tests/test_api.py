from datetime import datetime, timedelta, timezone

from app.models import TicketType


def _iso_days_ago(reference: datetime, days_ago: int) -> str:
    return (reference - timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")


def test_predict_risk_endpoint_returns_high_risk_for_complaint_rule(client):
    now = datetime.now(timezone.utc)
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
                "ticket_type": TicketType.complaint.value,
                "created_at": _iso_days_ago(now, 2),
            },
            {
                "ticket_id": "T002",
                "ticket_type": TicketType.billing.value,
                "created_at": _iso_days_ago(now, 10),
            },
            {
                "ticket_id": "T003",
                "ticket_type": TicketType.technical.value,
                "created_at": _iso_days_ago(now, 15),
            },
        ],
    }

    response = client.post("/predict-risk", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["customer_id"] == "C100"
    assert body["risk"] == "High"
    assert "reasons" in body
    assert any("Month-to-Month" in reason for reason in body["reasons"])


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "telco_rule_engine_http_requests_total" in response.text
