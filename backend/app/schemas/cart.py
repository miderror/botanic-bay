# backend/app/schemas/cart.py
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SCartItemBase(BaseModel):
    """Базовая схема элемента корзины"""

    product_id: UUID = Field(..., description="ID товара")
    quantity: int = Field(..., description="Количество товара", gt=0)


class SCartItem(SCartItemBase):
    """Схема для отображения элемента корзины"""

    id: UUID
    price: Decimal = Field(..., description="Цена товара")
    subtotal: Decimal = Field(..., description="Стоимость позиции")
    product_name: str = Field(..., description="Название товара")
    image_url: Optional[str] = Field(None, description="URL изображения товара")

    class Config:
        from_attributes = True


class SCart(BaseModel):
    """Схема для отображения корзины"""

    id: UUID
    items: List[SCartItem]
    total: Decimal = Field(..., description="Общая стоимость")
    expires_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class SAddToCart(SCartItemBase):
    """Схема для добавления товара в корзину"""

    pass


class SUpdateCartItem(BaseModel):
    """Схема для обновления количества товара в корзине"""

    quantity: int = Field(..., description="Новое количество товара", gt=0)


class SCartResponse(BaseModel):
    """Схема ответа при операциях с корзиной"""

    cart: Optional[SCart]  # Возвращаем строгую типизацию
    message: str = Field(..., description="Сообщение о результате операции")

    class Config:
        from_attributes = True
