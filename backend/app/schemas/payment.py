# backend/app/schemas/payment.py
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import UUID4, BaseModel, Field


class PaymentProvider(str, Enum):
    """Поддерживаемые платежные системы"""

    YOOKASSA = "yookassa"
    CASH = "cash"
    # Другие платежные системы могут быть добавлены здесь


class PaymentStatus(str, Enum):
    """Статусы платежей"""

    PENDING = "pending"
    WAITING_FOR_CAPTURE = "waiting_for_capture"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    FAILED = "failed"

    @classmethod
    def get_all_statuses(cls) -> List[str]:
        """Получение всех возможных статусов"""
        return [status.value for status in cls]


class SPaymentBase(BaseModel):
    """Базовая схема платежа"""

    provider: str = Field(..., description="Платежная система")
    amount: Decimal = Field(..., description="Сумма платежа")
    currency: str = Field("RUB", description="Валюта платежа")
    payment_method: Optional[str] = Field(None, description="Метод оплаты")


class SPaymentCreate(SPaymentBase):
    """Схема для создания платежа"""

    order_id: UUID4 = Field(..., description="ID заказа")
    return_url: Optional[str] = Field(None, description="URL возврата после оплаты")


class SPayment(SPaymentBase):
    """Схема для отображения платежа"""

    id: UUID4 = Field(..., description="ID платежа")
    order_id: UUID4 = Field(..., description="ID заказа")
    status: str = Field(..., description="Статус платежа")
    provider_payment_id: Optional[str] = Field(
        None, description="ID платежа в системе провайдера"
    )
    confirmation_url: Optional[str] = Field(
        None, description="URL для подтверждения оплаты"
    )
    payment_data: Optional[Dict[str, Any]] = Field(
        None, description="Дополнительные данные платежа"
    )
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")
    paid_at: Optional[datetime] = Field(None, description="Дата оплаты")
    refunded_at: Optional[datetime] = Field(None, description="Дата возврата")

    class Config:
        from_attributes = True


class SPaymentUpdate(BaseModel):
    """Схема для обновления платежа"""

    status: Optional[str] = Field(None, description="Статус платежа")
    provider_payment_id: Optional[str] = Field(
        None, description="ID платежа в системе провайдера"
    )
    payment_data: Optional[Dict[str, Any]] = Field(
        None, description="Дополнительные данные платежа"
    )
    confirmation_url: Optional[str] = Field(
        None, description="URL для подтверждения оплаты"
    )


class SYookassaWebhookRequest(BaseModel):
    """Схема для получения вебхука от ЮКассы"""

    event: str = Field(..., description="Тип события")
    object: Dict[str, Any] = Field(..., description="Данные о платеже")


class SPaymentResponse(BaseModel):
    """Схема ответа для платежа"""

    payment_id: UUID4 = Field(..., description="ID платежа")
    confirmation_url: Optional[str] = Field(None, description="URL для оплаты")
    status: str = Field(..., description="Статус платежа")


class SWidgetPaymentResponse(SPaymentResponse):
    """Схема ответа для платежа с виджетом"""

    confirmation_token: str = Field(..., description="Токен для инициализации виджета")
