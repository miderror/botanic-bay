import uuid
from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from .base import Base


class Product(Base):
    """
    Модель товара в каталоге

    Attributes:
        id: Уникальный идентификатор товара
        name: Название товара
        description: Описание товара
        price: Цена товара в рублях
        stock: Количество товара на складе
        is_active: Статус активности товара
        category: Категория товара
        image_url: URL изображения товара
        sku: Артикул товара
    """

    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    additional_description = Column(
        Text, nullable=True, comment="Дополнительное описание товара"
    )
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    # category = Column(String(100), nullable=True, index=True)
    image_url = Column(String(500), nullable=True)
    background_image_url = Column(
        String(500), nullable=True, comment="URL фоновой картинки товара"
    )
    sku = Column(String(50), unique=True, nullable=True)

    weight = Column(Integer, nullable=True, comment="Вес в граммах")
    length = Column(Integer, nullable=True, comment="Длина в мм")
    width = Column(Integer, nullable=True, comment="Ширина в мм")
    height = Column(Integer, nullable=True, comment="Высота в мм")

    # Добавляем поле для дополнительных изображений
    additional_images_urls = Column(
        ARRAY(String),
        nullable=True,
        server_default="{}",  # Пустой массив по умолчанию
        comment="URLs дополнительных изображений товара",
    )

    # Заменяем старое поле category на связь с моделью Category
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True
    )

    # Добавляем связь с категорией
    category = relationship("Category", back_populates="products", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Product {self.name}>"

    def dict(self) -> dict:
        """
        Преобразование в словарь для сериализации
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "additional_description": self.additional_description,
            "price": float(self.price),
            "stock": getattr(self, "available_quantity", self.stock),
            # Используем available_quantity если есть, иначе stock
            "is_active": self.is_active,
            "category": (
                self.category.name if self.category else None
            ),  # Берем только name
            "image_url": self.image_url,
            "background_image_url": self.background_image_url,
            "additional_images_urls": self.additional_images_urls or [],
            "sku": self.sku,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_admin_dict(self) -> dict:
        """
        Преобразование в словарь для админского интерфейса
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "stock": self.stock,
            "is_active": self.is_active,
            "category": self.category.name if self.category else None,
            "image_url": self.image_url,
            "background_image_url": self.background_image_url,
            "sku": self.sku,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "total_orders": 0,  # TODO: добавить реальную статистику
            "last_ordered_at": None,  # TODO: добавить реальную статистику
        }

    @property
    def category_name(self) -> Optional[str]:
        """
        Геттер для получения имени категории
        Сохраняет обратную совместимость со старым кодом
        """
        return self.category.name if self.category else None
