import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    and_,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.enums.referral import ReferralPayoutStatus
from app.models import Base


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    referrer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("referrals.id", ondelete="SET NULL"),
        nullable=True,
    )

    signed_conditions = Column(Boolean, nullable=False, default=False)
    signed_user_terms = Column(Boolean, nullable=False, default=False)

    user = relationship("User", backref="referral", lazy="selectin")

    children = relationship(
        "Referral",
        back_populates="referrer",
        lazy="select",
        foreign_keys=[referrer_id],
        cascade="all, delete-orphan",
    )
    referrer = relationship(
        "Referral",
        remote_side=[id],
        back_populates="children",
        lazy="selectin",
    )

    @hybrid_property
    def is_registered(self) -> bool:
        return self.signed_conditions and self.signed_user_terms

    @is_registered.expression
    def is_registered(cls):
        return and_(cls.signed_conditions.is_(True), cls.signed_user_terms.is_(True))

    def __repr__(self):
        return f"<Referral user_id={self.user_id} referrer_id={self.referrer_id}>"


class ReferralBonus(Base):
    __tablename__ = "referral_bonuses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referrer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("referrals.id", ondelete="CASCADE"),
        nullable=False,
    )
    referral_id = Column(
        UUID(as_uuid=True),
        ForeignKey("referrals.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )

    bonus_amount = Column(Numeric(10, 2), nullable=False)
    reverted_at = Column(
        DateTime(timezone=True), nullable=True
    )  # если реферал сделает возврат товара

    referrer = relationship(
        "Referral",
        foreign_keys=[referrer_id],
        lazy="selectin",
        backref="bonuses_as_referrer",
    )
    referral = relationship(
        "Referral",
        foreign_keys=[referral_id],
        lazy="selectin",
        backref="bonuses_as_referral",
    )
    order = relationship("Order", lazy="selectin")

    def __repr__(self):
        return (
            f"<ReferralBonus "
            f"referrer={self.referrer_id} "
            f"referral={self.referral_id} "
            f"bonus={self.bonus_amount}>"
        )


class ReferralPayoutRequest(Base):
    __tablename__ = "referral_payout_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_code = Column(String(11), nullable=False)
    account_number = Column(String(34), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(
        Enum(ReferralPayoutStatus),
        default=str(ReferralPayoutStatus.PENDING),
    )

    referrer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("referrals.id", ondelete="CASCADE"),
        nullable=False,
    )

    referrer = relationship(
        "Referral",
        backref="payout_requests",
        lazy="selectin",
    )
