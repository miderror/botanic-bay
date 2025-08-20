# backend/app/models/category.py
import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class Category(Base):
    """
    Модель категории товаров

    Attributes:
        id: Уникальный идентификатор категории
        name: Название категории
        description: Описание категории
        products: Связь с товарами в этой категории
    """

    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)

    # Связь с товарами
    products = relationship("Product", back_populates="category", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Category {self.name}>"

    def __str__(self) -> str:
        """
        Строковое представление категории
        """
        return self.name or ""

    def dict(self) -> str:
        """
        Преобразование категории в строку для сериализации
        """
        return self.name
