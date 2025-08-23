# backend/app/schemas/order.py
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.order_status import OrderStatus
from app.schemas.cdek.base import RequestLocation


# Обновленная схема пользователя для отображения в заказе
class SOrderUser(BaseModel):
    """Схема для отображения информации о пользователе в заказе"""

    id: UUID
    telegram_id: int
    username: Optional[str] = None
    full_name: str

    # Убираем поля email и phone, которых нет в модели

    class Config:
        from_attributes = True


class SOrderItemBase(BaseModel):
    """Базовая схема элемента заказа"""

    product_id: UUID
    quantity: int = Field(..., gt=0)
    price: Decimal


class SOrderItem(SOrderItemBase):
    """Схема для отображения элемента заказа"""

    id: UUID
    product_name: str
    subtotal: Decimal
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class SCreateOrder(BaseModel):
    """Схема для создания заказа"""

    # delivery_address: str = Field(..., min_length=10)
    address_id: Optional[UUID] = None
    delivery_point_id: Optional[UUID] = None
    delivery_method: str
    payment_method: str
    promo_code: Optional[str] = None


class SOrder(BaseModel):
    """Схема для отображения заказа"""

    id: UUID
    status: str
    items: List[SOrderItem]
    delivery_point: Optional[str]
    delivery_to_location: Optional[RequestLocation]
    delivery_method: str
    delivery_cost: Decimal
    subtotal: Decimal
    discount_amount: Optional[float] = 0.0
    promo_code: Optional[str] = None 
    total: Decimal
    planned_shipping_date: Optional[datetime]
    payment_method: Optional[str]
    payment_status: Optional[str]
    created_at: datetime
    updated_at: datetime
    user: SOrderUser  # Информация о пользователе, создавшем заказ

    @field_validator("status")
    def validate_status(cls, v):
        if v not in OrderStatus.get_all_statuses():
            raise ValueError(f"Invalid order status: {v}")
        return v

    class Config:
        from_attributes = True


class SOrderList(BaseModel):
    """Схема для списка заказов с пагинацией"""

    items: List[SOrder]
    total: int = Field(..., description="Общее количество заказов")
    page: int = Field(1, description="Текущая страница")
    size: int = Field(50, description="Размер страницы")
    pages: int = Field(..., description="Общее количество страниц")


class SUpdateOrderStatus(BaseModel):
    """Схема для обновления статуса заказа"""

    status: str = Field(..., description="Новый статус заказа")

    @field_validator("status")
    def validate_status(cls, v):
        if v not in OrderStatus.get_all_statuses():
            raise ValueError(f"Invalid order status: {v}")
        return v


class SOrderFilter(BaseModel):
    """Схема для фильтрации заказов"""

    status: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    min_total: Optional[Decimal] = None
    max_total: Optional[Decimal] = None

    @field_validator("status")
    def validate_status(cls, v):
        if v and v not in OrderStatus.get_all_statuses():
            raise ValueError(f"Invalid order status: {v}")
        return v


class SUserDeliveryPoint(BaseModel):
    id: UUID
    name: str
    address: str


class SUserAddress(BaseModel):
    id: Optional[UUID] = None
    latitude: float
    longitude: float
    address: str
    apartment: int
    entrance: Optional[int] = None
    floor: Optional[int] = None
    intercom_code: Optional[int] = None
    # is_default: bool
