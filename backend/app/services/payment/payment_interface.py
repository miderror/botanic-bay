# backend/app/services/payment/payment_interface.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.models.order import Order


class IPaymentProvider(ABC):
    """
    Интерфейс для платежных систем
    Обеспечивает стандартный набор методов для работы с разными платежными системами
    """

    @abstractmethod
    async def create_payment(
        self, order: Order, return_url: str, confirmation_type: str = "redirect"
    ) -> Dict[str, Any]:
        """
        Создание платежа

        Args:
            order: Заказ для оплаты
            return_url: URL возврата после оплаты
            confirmation_type: Тип подтверждения платежа (redirect или embedded)

        Returns:
            Dict[str, Any]: Данные созданного платежа
        """
        pass

    @abstractmethod
    async def check_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Проверка статуса платежа

        Args:
            payment_id: ID платежа в платежной системе

        Returns:
            Dict[str, Any]: Обновленные данные платежа
        """
        pass

    @abstractmethod
    async def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка уведомления от платежной системы

        Args:
            data: Данные уведомления

        Returns:
            Dict[str, Any]: Результат обработки
        """
        pass

    @abstractmethod
    async def refund_payment(
        self, payment_id: str, amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Возврат платежа

        Args:
            payment_id: ID платежа в платежной системе
            amount: Сумма возврата (если None, то полный возврат)

        Returns:
            Dict[str, Any]: Результат операции
        """
        pass
