from datetime import datetime, timedelta, timezone

from app.models import ContractType, CustomerProfile, RiskCategory, RiskRequest, Ticket, TicketType
from app.rules import evaluate_risk


def build_ticket(ticket_id: str, days_ago: int, ticket_type: TicketType = TicketType.technical) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        ticket_type=ticket_type,
        created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )


def build_customer(
    contract_type: ContractType = ContractType.one_year,
    monthly_charges: float = 75.0,
    previous_monthly_charges: float = 70.0,
) -> CustomerProfile:
    return CustomerProfile(
        customer_id="C001",
        contract_type=contract_type,
        monthly_charges=monthly_charges,
        previous_monthly_charges=previous_monthly_charges,
        tenure_months=12,
    )


def test_high_risk_for_more_than_five_recent_tickets():
    payload = RiskRequest(
        customer=build_customer(),
        tickets=[build_ticket(f"T{i}", i) for i in range(6)],
    )

    result = evaluate_risk(payload)

    assert result.risk == RiskCategory.high
    assert any("More than 5 support tickets" in reason for reason in result.reasons)


def test_medium_risk_for_charge_increase_and_three_tickets():
    payload = RiskRequest(
        customer=build_customer(monthly_charges=90.0, previous_monthly_charges=70.0),
        tickets=[build_ticket(f"T{i}", i) for i in range(3)],
    )

    result = evaluate_risk(payload)

    assert result.risk == RiskCategory.medium


def test_high_risk_for_month_to_month_complaint():
    payload = RiskRequest(
        customer=build_customer(
            contract_type=ContractType.month_to_month,
            monthly_charges=60.0,
            previous_monthly_charges=60.0,
        ),
        tickets=[build_ticket("T1", 2, TicketType.complaint)],
    )

    result = evaluate_risk(payload)

    assert result.risk == RiskCategory.high


def test_low_risk_when_no_rules_match():
    payload = RiskRequest(
        customer=build_customer(monthly_charges=70.0, previous_monthly_charges=70.0),
        tickets=[build_ticket("T1", 45)],
    )

    result = evaluate_risk(payload)

    assert result.risk == RiskCategory.low

