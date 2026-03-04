from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from app.models import RiskRequest, Ticket, TicketType


TICKET_TYPE_COLUMNS = [
    "complaint_ticket_count_90d",
    "technical_ticket_count_90d",
    "billing_ticket_count_90d",
    "general_ticket_count_90d",
]

NUMERIC_FEATURE_COLUMNS = [
    "ticket_frequency_7d",
    "ticket_frequency_30d",
    "ticket_frequency_90d",
    "ticket_sentiment_score",
    "complaint_ticket_count_90d",
    "technical_ticket_count_90d",
    "billing_ticket_count_90d",
    "general_ticket_count_90d",
    "avg_days_between_tickets_90d",
    "monthly_charge_change",
    "monthly_charges",
    "tenure_months",
]

CATEGORICAL_FEATURE_COLUMNS = ["contract_type"]
MODEL_FEATURE_COLUMNS = CATEGORICAL_FEATURE_COLUMNS + NUMERIC_FEATURE_COLUMNS


def default_sentiment(ticket_type: TicketType | str) -> float:
    ticket_value = ticket_type.value if isinstance(ticket_type, TicketType) else ticket_type
    return {
        "complaint": -0.85,
        "technical": -0.35,
        "billing": -0.25,
        "general": 0.2,
    }.get(ticket_value, 0.0)


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _average_gap_days(tickets: list[Ticket]) -> float:
    if len(tickets) < 2:
        return 90.0

    ordered = sorted(_normalize_timestamp(ticket.created_at) for ticket in tickets)
    gaps = []
    for previous, current in zip(ordered, ordered[1:]):
        gaps.append((current - previous).total_seconds() / 86400)
    return round(sum(gaps) / len(gaps), 4)


def build_feature_row(payload: RiskRequest, reference_time: datetime | None = None) -> dict[str, float | str]:
    now = _normalize_timestamp(reference_time or datetime.now(timezone.utc))
    tickets = [ticket for ticket in payload.tickets]

    window_7d = now - timedelta(days=7)
    window_30d = now - timedelta(days=30)
    window_90d = now - timedelta(days=90)
    recent_90d = [ticket for ticket in tickets if _normalize_timestamp(ticket.created_at) >= window_90d]

    sentiment_values = [
        ticket.sentiment_score if ticket.sentiment_score is not None else default_sentiment(ticket.ticket_type)
        for ticket in recent_90d
    ]
    category_counts = {
        "complaint_ticket_count_90d": 0,
        "technical_ticket_count_90d": 0,
        "billing_ticket_count_90d": 0,
        "general_ticket_count_90d": 0,
    }
    for ticket in recent_90d:
        category_counts[f"{ticket.ticket_type.value}_ticket_count_90d"] += 1

    return {
        "contract_type": payload.customer.contract_type.value,
        "ticket_frequency_7d": sum(
            1 for ticket in tickets if _normalize_timestamp(ticket.created_at) >= window_7d
        ),
        "ticket_frequency_30d": sum(
            1 for ticket in tickets if _normalize_timestamp(ticket.created_at) >= window_30d
        ),
        "ticket_frequency_90d": len(recent_90d),
        "ticket_sentiment_score": round(
            sum(sentiment_values) / len(sentiment_values), 4
        )
        if sentiment_values
        else 0.0,
        "avg_days_between_tickets_90d": _average_gap_days(recent_90d),
        "monthly_charge_change": round(
            payload.customer.monthly_charges - payload.customer.previous_monthly_charges, 4
        ),
        "monthly_charges": payload.customer.monthly_charges,
        "tenure_months": payload.customer.tenure_months,
        **category_counts,
    }


def build_feature_frame(payload: RiskRequest, reference_time: datetime | None = None) -> pd.DataFrame:
    return pd.DataFrame([build_feature_row(payload, reference_time=reference_time)], columns=MODEL_FEATURE_COLUMNS)

