# backend/app/schemas/admin.py
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, conlist, field_validator

from app.core.constants import UserRoles
from app.schemas.order import SOrder

from .product import SProduct
from .user import SUser


class SAdminProductFilter(BaseModel):
    """Схема для фильтрации товаров в админке"""

    name: Optional[str] = Field(None, description="Фильтр по названию товара")
    category: Optional[str] = Field(None, description="Фильтр по категории")
    is_active: Optional[bool] = Field(None, description="Фильтр по статусу активности")


class SAdminProductResponse(SProduct):
    """
    Расширенная схема товара для админского интерфейса
    Наследуется от базовой схемы товара и добавляет админские поля
    """

    category: Optional[str] = Field(None, description="Название категории товара")
    total_orders: int = Field(0, description="Количество заказов товара")
    last_ordered_at: Optional[datetime] = Field(
        None, description="Дата последнего заказа"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Витамин C",
                "image_url": "https://example.com/image.jpg",
                "background_image_url": "https://example.com/bg.jpg",
                "description": "Витамин C 1000мг, 100 таблеток",
                "price": "999.99",
                "stock": 100,
                "is_active": True,
                "category": "Витамины",
                "total_orders": 42,
                "last_ordered_at": "2024-02-05T12:00:00",
                "created_at": "2024-02-05T12:00:00",
                "updated_at": "2024-02-05T12:00:00",
            }
        }


class SAdminProductList(BaseModel):
    """Схема для списка товаров в админке с пагинацией"""

    items: List[SAdminProductResponse]
    total: int = Field(..., description="Общее количество товаров")
    page: int = Field(1, description="Текущая страница")
    size: int = Field(50, description="Размер страницы")
    pages: int = Field(..., description="Общее количество страниц")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Витамин C",
                        "price": "999.99",
                        "stock": 100,
                        "is_active": True,
                        "total_orders": 42,
                        "last_ordered_at": "2024-02-05T12:00:00",
                    }
                ],
                "total": 100,
                "page": 1,
                "size": 50,
                "pages": 2,
            }
        }


class SAdminUserFilter(BaseModel):
    """Схема для фильтрации пользователей в админке"""

    username: Optional[str] = Field(None, description="Фильтр по имени пользователя")
    telegram_id: Optional[int] = Field(None, description="Фильтр по Telegram ID")
    role: Optional[str] = Field(None, description="Фильтр по роли")
    is_active: Optional[bool] = Field(None, description="Фильтр по статусу активности")


class SAdminUserResponse(SUser):
    """
    Расширенная схема пользователя для админского интерфейса
    Добавляет поля, которые видны только администраторам
    """

    total_orders: int = Field(0, description="Количество заказов пользователя")
    total_spent: float = Field(0, description="Общая сумма покупок")
    last_order_at: Optional[datetime] = Field(
        None, description="Дата последнего заказа"
    )
    roles: List[str] = Field(
        default_factory=list, description="Список ролей пользователя"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "telegram_id": 123456789,
                "username": "john_doe",
                "full_name": "John Doe",
                "roles": ["user"],
                "total_orders": 5,
                "total_spent": 9999.99,
                "last_order_at": "2024-02-05T12:00:00",
                "created_at": "2024-02-05T12:00:00",
            }
        }


class SAdminUserList(BaseModel):
    """Схема для списка пользователей в админке с пагинацией"""

    items: List[SAdminUserResponse]
    total: int = Field(..., description="Общее количество пользователей")
    page: int = Field(1, description="Текущая страница")
    size: int = Field(50, description="Размер страницы")
    pages: int = Field(..., description="Общее количество страниц")


class SUpdateUserRoles(BaseModel):
    """Схема для обновления ролей пользователя"""

    roles: conlist(str, min_length=1) = Field(
        ..., description="Список ролей пользователя", example=["user", "admin"]
    )

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: List[str]) -> List[str]:
        """Проверяем что все роли существуют"""
        valid_roles = UserRoles.get_all_roles()
        for role in v:
            if role not in valid_roles:
                raise ValueError(f"Invalid role: {role}")
        return v

    class Config:
        json_schema_extra = {"example": {"roles": ["user", "admin"]}}


class SAdminOrderFilter(BaseModel):
    """Схема для фильтрации заказов в админке"""

    order_id: Optional[UUID] = None
    status: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    min_total: Optional[Decimal] = None
    max_total: Optional[Decimal] = None


class SAdminOrderList(BaseModel):
    """Схема для списка заказов в админке с пагинацией"""

    items: List[SOrder]
    total: int
    page: int
    size: int
    pages: int


class SUpdateOrderStatus(BaseModel):
    status: str
    comment: Optional[str] = None
