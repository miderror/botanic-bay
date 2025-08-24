import uuid
from typing import List

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Table,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.constants import UserRoles

from ..schemas.user import UserDiscountLevel
from .base import Base

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)

    users = relationship(
        "User", secondary=user_roles, back_populates="roles", lazy="selectin"
    )

    @classmethod
    def get_role_by_name(cls, name: str) -> "Role":
        """Get role by name, validating against UserRoles enum"""
        if name not in UserRoles.get_all_roles():
            raise ValueError(f"Invalid role name: {name}")
        return cls(name=name)

    @property
    def role_names(self) -> List[str]:
        """
        Получить список названий ролей пользователя

        Returns:
            List[str]: Список названий ролей
        """
        return [role.name for role in self.roles]

    def __repr__(self):
        return f"<Role {self.name}>"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, unique=True)
    full_name = Column(String)
    referral_code = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    bonus_balance = Column(Numeric(10, 2), nullable=False, default=0.00)
    monthly_spent = Column(Numeric(10, 2), nullable=False, default=0.00)
    payment_details = Column(String, nullable=True)
    accepted_terms = Column(Boolean, default=False)

    profile = relationship(
        "UserProfile",
        back_populates="user",
        lazy="joined",
        cascade="all, delete-orphan",
    )
    discount = relationship(
        "UserDiscount",
        back_populates="user",
        lazy="joined",
        cascade="all, delete-orphan",
    )
    referral = relationship(
        "Referral", back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    payout_requests = relationship(
        "PayoutRequest", back_populates="user", cascade="all, delete-orphan"
    )

    invited_by = relationship("User", remote_side=[id], backref="referrals")

    @property
    def role_names(self) -> List[str]:
        """
        Получить список названий ролей пользователя

        Returns:
            List[str]: Список названий ролей
        """
        return [role.name for role in self.roles]

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )

    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        return any(role.name == role_name for role in self.roles)

    def add_role(self, role_name: str) -> None:
        """Add role to user"""
        if not self.has_role(role_name):
            if role_name not in UserRoles.get_all_roles():
                raise ValueError(f"Invalid role name: {role_name}")
            self.roles.append(Role(name=role_name))

    def remove_role(self, role_name: str) -> None:
        """Remove role from user"""
        self.roles = [role for role in self.roles if role.name != role_name]

    def __repr__(self):
        return f"<User {self.username}>"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=True)

    user = relationship("User", back_populates="profile", lazy="joined")


class UserDiscount(Base):
    __tablename__ = "user_discounts"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    current_level = Column(
        Enum(UserDiscountLevel, name="userdiscountlevel"),
        nullable=False,
        default=UserDiscountLevel.NONE,
    )
    last_purchase_date = Column(Date, nullable=True)

    user = relationship("User", back_populates="discount", lazy="joined")
