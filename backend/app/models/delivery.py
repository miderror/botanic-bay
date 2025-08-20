# backend/app/models/order.py
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.logger import logger
from app.models.base import Base
from app.models.order_status import OrderStatus
from app.schemas.cdek.enums import OfficeType


class CDEKDeliveryPoint(Base):
    __tablename__ = "cdek_delivery_points"

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    code = Column(String, nullable=False)
    type = Column(Enum(OfficeType), nullable=False)
    address = Column(String, nullable=False)

    @property
    def point_name(self) -> str:
        point_toponyms = {
            OfficeType.PVZ: "ПВЗ",
            OfficeType.POSTAMAT: "Постамат",
            OfficeType.ALL: "",
        }
        return f"{point_toponyms[self.type]} {self.code}"


class UserDeliveryPoint(Base):
    __tablename__ = "user_delivery_points"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "cdek_delivery_point_id",
            name="uix_user_cdek_dp",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    cdek_delivery_point_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cdek_delivery_points.id", ondelete="CASCADE"),
    )
    user = relationship("User", backref="delivery_points")
    cdek_delivery_point = relationship("CDEKDeliveryPoint")

    @property
    def name(self) -> str:
        return self.cdek_delivery_point.point_name

    @property
    def address(self) -> str:
        return self.cdek_delivery_point.address


class UserAddress(Base):
    __tablename__ = "user_addresses"
    __table_args__ = (UniqueConstraint("user_id", "address", name="uix_user_address"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )

    address = Column(String(), nullable=False)
    apartment = Column(Integer(), nullable=False)
    entrance = Column(Integer(), nullable=True)
    floor = Column(Integer(), nullable=True)
    intercom_code = Column(Integer(), nullable=True)

    latitude = Column(Float())
    longitude = Column(Float())

    user = relationship("User", backref="addresses")
