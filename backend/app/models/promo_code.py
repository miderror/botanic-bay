import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class PromoCode(Base):
    """Модель промокода"""

    __tablename__ = "promo_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    discount_percent = Column(Numeric(5, 2), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    max_uses = Column(Integer, default=1)
    uses_left = Column(Integer, default=1)

    def __repr__(self) -> str:
        return f"<PromoCode {self.code}>"