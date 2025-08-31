import os
import uuid
from typing import Optional

from fastapi_storages import FileSystemStorage
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.core.logger import logger
from app.core.settings import settings

from .base import Base
from .custom_types import ResilientImageType

storage = FileSystemStorage(path=str(settings.MEDIA_DIR / "products"))


class ProductImage(Base):
    """Модель для хранения дополнительных изображений."""

    __tablename__ = "product_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )

    image_url = Column(ResilientImageType(storage=storage), nullable=False)

    position = Column(Integer, default=0)

    product = relationship("Product", back_populates="additional_images")


class Product(Base):
    """
    Модель товара в каталоге
    """

    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    additional_description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    image_url = Column(ResilientImageType(storage=storage), nullable=True)
    background_image_url = Column(ResilientImageType(storage=storage), nullable=True)

    sku = Column(String(50), unique=True, nullable=True)
    weight = Column(Integer, nullable=True)
    length = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    # additional_images_urls = Column(ARRAY(String), nullable=True, server_default="{}")
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True
    )
    category = relationship("Category", back_populates="products", lazy="selectin")
    additional_images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.position",
    )

    def __repr__(self) -> str:
        return f"<Product {self.name}>"

    def dict(self) -> dict:
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
            "additional_images_urls": [str(img.image_url) for img in self.additional_images if img.image_url],
            "sku": self.sku,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @property
    def category_name(self) -> Optional[str]:
        return self.category.name if self.category else None
