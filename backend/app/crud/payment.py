# backend/app/crud/payment.py
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.payment import Payment
from app.schemas.payment import SPaymentCreate, SPaymentUpdate
from app.utils.json_helpers import (  # Импортируем утилиту для сериализации JSON
    serialize_for_json,
)


class PaymentCRUD:
    """CRUD операции для работы с платежами"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_payment(self, payment_data: SPaymentCreate) -> Payment:
        """
        Создание нового платежа

        Args:
            payment_data: Данные для создания платежа

        Returns:
            Payment: Созданный платеж
        """
        # Преобразуем данные из схемы в словарь
        payment_dict = payment_data.model_dump(exclude_unset=True)

        # Сериализуем payment_data, если она есть
        if "payment_data" in payment_dict and payment_dict["payment_data"]:
            payment_dict["payment_data"] = serialize_for_json(
                payment_dict["payment_data"]
            )

        # Создаем объект платежа
        payment = Payment(**payment_dict)

        # Сохраняем в базу данных
        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)

        logger.info(
            "Created new payment",
            extra={
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
                "provider": payment.provider,
                "amount": str(payment.amount),
            },
        )

        return payment

    async def get_payment(self, payment_id: UUID) -> Optional[Payment]:
        """
        Получение платежа по ID

        Args:
            payment_id: ID платежа

        Returns:
            Optional[Payment]: Платеж или None если не найден
        """
        query = select(Payment).where(Payment.id == payment_id)
        result = await self.session.execute(query)
        payment = result.scalar_one_or_none()

        return payment

    async def get_payment_by_provider_id(
        self, provider: str, provider_payment_id: str
    ) -> Optional[Payment]:
        """
        Получение платежа по ID провайдера

        Args:
            provider: Название платежной системы
            provider_payment_id: ID платежа в системе провайдера

        Returns:
            Optional[Payment]: Платеж или None если не найден
        """
        query = select(Payment).where(
            and_(
                Payment.provider == provider,
                Payment.provider_payment_id == provider_payment_id,
            )
        )
        result = await self.session.execute(query)
        payment = result.scalar_one_or_none()

        return payment

    async def update_payment(
        self, payment_id: UUID, payment_data: SPaymentUpdate
    ) -> Optional[Payment]:
        """
        Обновление данных платежа

        Args:
            payment_id: ID платежа
            payment_data: Данные для обновления

        Returns:
            Optional[Payment]: Обновленный платеж или None если не найден
        """
        payment = await self.get_payment(payment_id)
        if not payment:
            return None

        # Получаем данные для обновления
        update_data = payment_data.model_dump(exclude_unset=True)

        # Если есть статус, обрабатываем его особым образом
        if "status" in update_data:
            payment.update_status(update_data["status"])
            del update_data["status"]

        # Обрабатываем payment_data для корректной сериализации в JSON
        if "payment_data" in update_data and update_data["payment_data"]:
            # Сериализуем сложные типы данных для хранения в JSON
            update_data["payment_data"] = serialize_for_json(
                update_data["payment_data"]
            )

        # Обновляем остальные поля
        for key, value in update_data.items():
            setattr(payment, key, value)

        # Сохраняем изменения
        await self.session.commit()
        await self.session.refresh(payment)

        logger.info(
            "Updated payment",
            extra={
                "payment_id": str(payment.id),
                "updated_fields": list(update_data.keys()),
            },
        )

        return payment

    async def get_order_payments(self, order_id: UUID) -> List[Payment]:
        """
        Получение всех платежей для заказа

        Args:
            order_id: ID заказа

        Returns:
            List[Payment]: Список платежей
        """
        # Выбираем все платежи для заказа, отсортированные по дате создания (новые сначала)
        query = (
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(desc(Payment.created_at))
        )
        result = await self.session.execute(query)
        payments = result.scalars().all()

        return payments

    async def get_last_order_payment(self, order_id: UUID) -> Optional[Payment]:
        """
        Получение последнего платежа для заказа

        Args:
            order_id: ID заказа

        Returns:
            Optional[Payment]: Последний платеж или None
        """
        # Выбираем самый последний платеж для заказа
        query = (
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(desc(Payment.created_at))
            .limit(1)
        )
        result = await self.session.execute(query)
        payment = result.scalar_one_or_none()

        return payment
