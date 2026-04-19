from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import ContractType, CustomerProfile, RiskRequest, Ticket, TicketType


FIXED_NOW = datetime(2026, 3, 22, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def fixed_now() -> datetime:
    return FIXED_NOW


@pytest.fixture
def customer_factory():
    def _build(
        *,
        contract_type: ContractType = ContractType.one_year,
        monthly_charges: float = 75.0,
        previous_monthly_charges: float = 70.0,
        tenure_months: int = 12,
        customer_id: str = "C001",
    ) -> CustomerProfile:
        return CustomerProfile(
            customer_id=customer_id,
            contract_type=contract_type,
            monthly_charges=monthly_charges,
            previous_monthly_charges=previous_monthly_charges,
            tenure_months=tenure_months,
        )

    return _build


@pytest.fixture
def ticket_factory(fixed_now: datetime):
    def _build(
        ticket_id: str,
        *,
        days_ago: int,
        ticket_type: TicketType = TicketType.technical,
    ) -> Ticket:
        return Ticket(
            ticket_id=ticket_id,
            ticket_type=ticket_type,
            created_at=fixed_now - timedelta(days=days_ago),
        )

    return _build


@pytest.fixture
def request_factory(customer_factory, ticket_factory):
    def _build(
        *,
        contract_type: ContractType = ContractType.one_year,
        monthly_charges: float = 75.0,
        previous_monthly_charges: float = 70.0,
        ticket_specs: list[dict] | None = None,
        customer_id: str = "C001",
    ) -> RiskRequest:
        tickets = [
            ticket_factory(
                spec["ticket_id"],
                days_ago=spec["days_ago"],
                ticket_type=spec.get("ticket_type", TicketType.technical),
            )
            for spec in (ticket_specs or [])
        ]
        return RiskRequest(
            customer=customer_factory(
                contract_type=contract_type,
                monthly_charges=monthly_charges,
                previous_monthly_charges=previous_monthly_charges,
                customer_id=customer_id,
            ),
            tickets=tickets,
        )

    return _build
