from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from app.enums.referral import ReferralPayoutStatus
from app.models import Referral


class ReferralLinkPayload(BaseModel):
    referral_code: str
    # referral_id: UUID


class ReferralChild(BaseModel):
    referral: "Referral"
    referral_count: int

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }


class ReferralChildBonus(BaseModel):
    referral: "Referral"
    current_month_orders: Optional[int] = None

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }


class SReferral(BaseModel):
    id: UUID
    full_name: str
    referral_bonus: float
    balance: Optional[float] = None
    referrals_count: Optional[int] = None
    signed_conditions: Optional[bool] = None
    signed_user_terms: Optional[bool] = None
    is_registered: Optional[bool] = None
    current_month_orders: Optional[int] = None
    invite_link: Optional[str] = None


class SReferrer(BaseModel):
    id: UUID
    full_name: str


class SListPaginated(BaseModel):
    items: list[Any] = []
    pages: int = 0
    total: int = 0
    size: int = 0


class SReferralListPaginated(SListPaginated):
    items: list[Optional[SReferral]] = []


class SReferralPayoutRequest(BaseModel):
    id: Optional[UUID] = None
    bank_code: str
    account_number: str
    amount: float
    status: Optional[ReferralPayoutStatus] = None
    referrer_id: Optional[UUID] = None
    referrer: Optional[SReferrer] = None
    created_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True,
    }


class SReferralPayoutRequestPaginated(SListPaginated):
    items: list[Optional[SReferralPayoutRequest]] = []
