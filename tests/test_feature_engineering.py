from datetime import datetime, timedelta, timezone

from app.feature_engineering import build_feature_row
from app.models import ContractType, CustomerProfile, RiskRequest, Ticket, TicketType


def test_build_feature_row_generates_required_ml_features():
    now = datetime.now(timezone.utc)
    payload = RiskRequest(
        customer=CustomerProfile(
            customer_id="C001",
            contract_type=ContractType.month_to_month,
            monthly_charges=95.0,
            previous_monthly_charges=80.0,
            tenure_months=8,
        ),
        tickets=[
            Ticket(
                ticket_id="T1",
                ticket_type=TicketType.complaint,
                created_at=now - timedelta(days=3),
                sentiment_score=-0.9,
            ),
            Ticket(
                ticket_id="T2",
                ticket_type=TicketType.billing,
                created_at=now - timedelta(days=10),
                sentiment_score=-0.4,
            ),
            Ticket(
                ticket_id="T3",
                ticket_type=TicketType.general,
                created_at=now - timedelta(days=40),
                sentiment_score=0.3,
            ),
        ],
    )

    features = build_feature_row(payload, reference_time=now)

    assert features["ticket_frequency_7d"] == 1
    assert features["ticket_frequency_30d"] == 2
    assert features["ticket_frequency_90d"] == 3
    assert features["complaint_ticket_count_90d"] == 1
    assert features["billing_ticket_count_90d"] == 1
    assert features["general_ticket_count_90d"] == 1
    assert features["monthly_charge_change"] == 15.0

