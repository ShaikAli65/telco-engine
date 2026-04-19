import pytest

from app.models import ContractType, RiskCategory, TicketType
from app.rules import evaluate_risk


@pytest.mark.parametrize(
    ("ticket_specs", "contract_type", "monthly_charges", "previous_monthly_charges", "expected_risk", "reason_fragment"),
    [
        (
            [{"ticket_id": f"T{i}", "days_ago": i} for i in range(6)],
            ContractType.one_year,
            75.0,
            70.0,
            RiskCategory.high,
            "More than 5 support tickets",
        ),
        (
            [{"ticket_id": f"T{i}", "days_ago": i} for i in range(3)],
            ContractType.one_year,
            90.0,
            70.0,
            RiskCategory.medium,
            "Monthly charges increased",
        ),
        (
            [{"ticket_id": "T1", "days_ago": 2, "ticket_type": TicketType.complaint}],
            ContractType.month_to_month,
            60.0,
            60.0,
            RiskCategory.high,
            "Month-to-Month customer",
        ),
        (
            [{"ticket_id": "T1", "days_ago": 45}],
            ContractType.one_year,
            70.0,
            70.0,
            RiskCategory.low,
            "No churn escalation rules matched",
        ),
    ],
)
def test_evaluate_risk_rules(
    request_factory,
    fixed_now,
    ticket_specs,
    contract_type,
    monthly_charges,
    previous_monthly_charges,
    expected_risk,
    reason_fragment,
):
    payload = request_factory(
        contract_type=contract_type,
        monthly_charges=monthly_charges,
        previous_monthly_charges=previous_monthly_charges,
        ticket_specs=ticket_specs,
    )

    result = evaluate_risk(payload, now=fixed_now)

    assert result.risk == expected_risk
    assert any(reason_fragment in reason for reason in result.reasons)


def test_evaluate_risk_ignores_old_complaint_tickets(request_factory, fixed_now):
    payload = request_factory(
        contract_type=ContractType.month_to_month,
        monthly_charges=80.0,
        previous_monthly_charges=80.0,
        ticket_specs=[
            {
                "ticket_id": "T-old",
                "days_ago": 31,
                "ticket_type": TicketType.complaint,
            }
        ],
    )

    result = evaluate_risk(payload, now=fixed_now)

    assert result.risk == RiskCategory.low
    assert result.reasons == ["No churn escalation rules matched the current profile and ticket history"]
