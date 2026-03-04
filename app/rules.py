from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.models import RiskCategory, RiskRequest


@dataclass(frozen=True)
class EvaluationResult:
    risk: RiskCategory
    reasons: list[str]


def evaluate_risk(payload: RiskRequest, now: datetime | None = None) -> EvaluationResult:
    current_time = now or datetime.now(timezone.utc)
    last_30_days = current_time - timedelta(days=30)
    recent_tickets = [ticket for ticket in payload.tickets if ticket.created_at >= last_30_days]
    complaint_tickets = [ticket for ticket in recent_tickets if ticket.ticket_type.value == "complaint"]

    reasons: list[str] = []

    if len(recent_tickets) > 5:
        reasons.append("More than 5 support tickets raised in the last 30 days")

    charges_increased = payload.customer.monthly_charges > payload.customer.previous_monthly_charges
    if charges_increased and len(recent_tickets) >= 3:
        reasons.append("Monthly charges increased and at least 3 tickets were raised recently")

    if payload.customer.contract_type.value == "Month-to-Month" and complaint_tickets:
        reasons.append("Month-to-Month customer raised at least one complaint ticket")

    if any("More than 5" in reason for reason in reasons):
        return EvaluationResult(risk=RiskCategory.high, reasons=reasons)

    if any("Month-to-Month" in reason for reason in reasons):
        return EvaluationResult(risk=RiskCategory.high, reasons=reasons)

    if any("Monthly charges increased" in reason for reason in reasons):
        return EvaluationResult(risk=RiskCategory.medium, reasons=reasons)

    return EvaluationResult(
        risk=RiskCategory.low,
        reasons=["No churn escalation rules matched the current profile and ticket history"],
    )

