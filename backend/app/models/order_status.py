# backend/app/models/order_status.py
from enum import Enum
from typing import Set


class OrderStatus(str, Enum):
    """Статусы заказа"""

    PENDING = "pending"  # Ожидает оплаты
    PAID = "paid"  # Оплачен
    PROCESSING = "processing"  # В обработке
    SHIPPED = "shipped"  # Отправлен
    DELIVERED = "delivered"  # Доставлен
    CANCELLED = "cancelled"  # Отменен

    @classmethod
    def get_all_statuses(cls) -> Set[str]:
        """Получение всех доступных статусов"""
        return {status.value for status in cls}

    @classmethod
    def get_active_statuses(cls) -> Set[str]:
        """Получение статусов активных заказов"""
        return {
            cls.PENDING.value,
            cls.PAID.value,
            cls.PROCESSING.value,
            cls.SHIPPED.value,
        }

    @classmethod
    def get_final_statuses(cls) -> Set[str]:
        """Получение финальных статусов"""
        return {cls.DELIVERED.value, cls.CANCELLED.value}
