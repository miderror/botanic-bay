from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SPromoCodeBase(BaseModel):
    code: str = Field(..., max_length=50)
    discount_percent: Decimal = Field(..., gt=0, le=100)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    max_uses: int = Field(1, gt=0)
    uses_left: int = Field(1, gt=0)

class SPromoCodeCreate(SPromoCodeBase):
    pass

class SPromoCodeUpdate(BaseModel):
    discount_percent: Optional[Decimal] = Field(None, gt=0, le=100)
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    max_uses: Optional[int] = Field(None, gt=0)
    uses_left: Optional[int] = Field(None, ge=0)


class SPromoCode(SPromoCodeBase):
    id: UUID

    class Config:
        from_attributes = True

class SPromoCodeApply(BaseModel):
    code: str

class SPromoCodeApplyResponse(BaseModel):
    code: str
    discount_percent: float
    is_valid: bool
    message: str