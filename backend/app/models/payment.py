# backend/app/models/payment.py
from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Payment(Base):
    """
    Модель платежа в системе
    Хранит информацию о платежах и их статусах
    """

    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    provider = Column(String, nullable=False, comment="Название платежной системы")
    provider_payment_id = Column(
        String, nullable=True, comment="ID платежа в системе провайдера"
    )
    status = Column(String, nullable=False, default="pending")
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="RUB", nullable=False)
    payment_method = Column(String, nullable=True, comment="Метод оплаты")
    payment_data = Column(
        JSON, nullable=True, comment="Дополнительные данные об оплате"
    )
    confirmation_url = Column(
        String, nullable=True, comment="URL для подтверждения оплаты"
    )
    paid_at = Column(
        DateTime(timezone=True), nullable=True, comment="Дата и время оплаты"
    )
    refunded_at = Column(
        DateTime(timezone=True), nullable=True, comment="Дата и время возврата"
    )

    # Связь с заказом
    order = relationship("Order", back_populates="payments")

    def update_status(self, new_status: str) -> None:
        """
        Обновление статуса платежа

        Args:
            new_status: Новый статус платежа
        """
        from app.core.logger import logger

        old_status = self.status
        self.status = new_status

        # Обновляем дату оплаты для успешного платежа
        if new_status == "succeeded" and old_status != "succeeded":
            self.paid_at = datetime.now().astimezone()

        # Обновляем дату возврата для отмененного/возвращенного платежа
        if new_status in ["refunded", "canceled"] and old_status not in [
            "refunded",
            "canceled",
        ]:
            self.refunded_at = datetime.now().astimezone()

        logger.info(
            "Payment status updated",
            extra={
                "payment_id": str(self.id),
                "provider": self.provider,
                "order_id": str(self.order_id),
                "old_status": old_status,
                "new_status": new_status,
            },
        )
