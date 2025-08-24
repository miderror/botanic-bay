# backend/app/schemas/product.py
from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, condecimal


class SProductBase(BaseModel):
    """Базовая схема товара"""

    name: str = Field(..., description="Название товара", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Описание товара")
    additional_description: Optional[str] = Field(
        None, description="Дополнительное описание товара"
    )
    price: condecimal(decimal_places=2, gt=0) = Field(
        ..., description="Цена товара в рублях"
    )
    stock: int = Field(0, description="Количество товара на складе", ge=0)
    is_active: bool = Field(True, description="Статус активности товара")
    category: Optional[str] = Field(
        None, description="Название категории товара"
    )  # Явно указываем строку
    image_url: Optional[str] = Field(None, description="URL изображения товара")
    background_image_url: Optional[str] = Field(
        None, description="URL фоновой картинки товара"
    )
    weight: Optional[int] = Field(None, description="Вес в граммах", ge=0)
    length: Optional[int] = Field(None, description="Длина в мм", ge=0)
    width: Optional[int] = Field(None, description="Ширина в мм", ge=0)
    height: Optional[int] = Field(None, description="Высота в мм", ge=0)

    additional_images_urls: Optional[List[str]] = Field(
        default_factory=list, description="Список URL дополнительных изображений товара"
    )

    class Config:
        from_attributes = True


class SProductCreate(SProductBase):
    """Схема для создания товара"""

    pass


class SProductUpdate(BaseModel):
    """Схема для обновления товара"""

    name: Optional[str] = Field(
        None, description="Название товара", min_length=1, max_length=255
    )
    description: Optional[str] = Field(None, description="Описание товара")
    additional_description: Optional[str] = Field(
        None, description="Дополнительное описание товара"
    )
    price: Optional[condecimal(decimal_places=2, gt=0)] = Field(
        None, description="Цена товара в рублях"
    )
    stock: Optional[int] = Field(None, description="Количество товара на складе", ge=0)
    is_active: Optional[bool] = Field(None, description="Статус активности товара")
    category: Optional[str] = Field(None, description="Категория товара")
    image_url: Optional[str] = Field(
        None, description="URL изображения товара"
    )  # Добавляем это поле
    background_image_url: Optional[str] = Field(
        None, description="URL фоновой картинки товара"
    )
    additional_images_urls: Optional[List[str]] = Field(
        None, description="Список URL дополнительных изображений товара"
    )


class SProduct(SProductBase):
    """Схема для отображения товара"""

    id: UUID = Field(..., description="Уникальный идентификатор товара")
    category: Optional[str] = Field(None, description="Название категории товара")
    image_url: Optional[str] = Field(
        None, description="URL изображения товара"
    )  # Добавляем это поле
    background_image_url: Optional[str] = Field(
        None, description="URL фоновой картинки товара"
    )
    created_at: datetime = Field(..., description="Дата создания товара")
    updated_at: datetime = Field(..., description="Дата последнего обновления товара")

    class Config:
        from_attributes = True

        @staticmethod
        def schema_extra(schema: dict[str, Any]) -> None:
            """Дополнительные настройки схемы"""
            props = schema.get("properties", {})
            if "category" in props:
                props["category"]["title"] = "Категория"

        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Витамин C",
                "description": "Витамин C 1000мг, 100 таблеток",
                "price": "999.99",
                "stock": 100,
                "is_active": True,
                "created_at": "2024-02-05T12:00:00",
                "updated_at": "2024-02-05T12:00:00",
            }
        }


class SProductList(BaseModel):
    """Схема для списка товаров с пагинацией"""

    items: list[SProduct] = Field(..., description="Список товаров")
    total: int = Field(..., description="Общее количество товаров")
    page: int = Field(1, description="Текущая страница")
    size: int = Field(10, description="Размер страницы")
    pages: int = Field(..., description="Общее количество страниц")

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Витамин C",
                        "description": "Витамин C 1000мг, 100 таблеток",
                        "price": "999.99",
                        "stock": 100,
                        "is_active": True,
                        "created_at": "2024-02-05T12:00:00",
                        "updated_at": "2024-02-05T12:00:00",
                    }
                ],
                "total": 100,
                "page": 1,
                "size": 10,
                "pages": 10,
            }
        }


class SCategoryList(BaseModel):
    """Схема для списка категорий"""

    categories: List[str]
