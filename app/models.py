from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ContractType(str, Enum):
    month_to_month = "Month-to-Month"
    one_year = "One year"
    two_year = "Two year"


class TicketType(str, Enum):
    complaint = "complaint"
    technical = "technical"
    billing = "billing"
    general = "general"


class RiskCategory(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class Ticket(BaseModel):
    ticket_id: str = Field(..., description="Unique support ticket identifier")
    ticket_type: TicketType
    created_at: datetime
    sentiment_score: float | None = Field(default=None, ge=-1, le=1)


class CustomerProfile(BaseModel):
    customer_id: str
    contract_type: ContractType
    monthly_charges: float = Field(..., ge=0)
    previous_monthly_charges: float = Field(..., ge=0)
    tenure_months: int = Field(..., ge=0)


class RiskRequest(BaseModel):
    customer: CustomerProfile
    tickets: list[Ticket] = Field(default_factory=list)


class RiskResponse(BaseModel):
    customer_id: str
    risk: RiskCategory
    churn_probability: float = Field(..., ge=0, le=1)
    model_version: str
    reasons: list[str]
    evaluated_at: datetime
