# backend/app/core/constants.py
from enum import Enum
from typing import Set


class UserRoles(str, Enum):
    """System user roles"""

    ADMIN = "admin"
    USER = "user"
    MANAGER = "manager"
    SUPPORT = "support"

    @classmethod
    def get_all_roles(cls) -> Set[str]:
        """Return set of all available roles"""
        return {role.value for role in cls}

    @classmethod
    def get_default_roles(cls) -> dict[str, str]:
        """Return dictionary of roles with their descriptions"""
        return {
            cls.ADMIN.value: "Administrator with full access",
            cls.USER.value: "Regular user",
            cls.MANAGER.value: "Store manager",
            cls.SUPPORT.value: "Customer support",
        }


class PaymentMethods(str, Enum):
    """Методы оплаты в системе"""

    BANK_CARD = "bank_card"
    YOOMONEY = "yoomoney"
    CASH = "cash"

    @classmethod
    def get_all_methods(cls) -> Set[str]:
        """Return set of all available payment methods"""
        return {method.value for method in cls}

    @classmethod
    def get_display_names(cls) -> dict[str, str]:
        """Return dictionary of payment methods with display names"""
        return {
            cls.BANK_CARD.value: "Банковская карта",
            cls.YOOMONEY.value: "ЮMoney",
            cls.CASH.value: "Наличные при получении",
        }


class PaymentStatuses(str, Enum):
    """Статусы платежей в системе"""

    PENDING = "pending"
    WAITING_FOR_CAPTURE = "waiting_for_capture"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    FAILED = "failed"


YOOKASSA_CONFIRMATION_TYPES = {"REDIRECT": "redirect", "EMBEDDED": "embedded"}
