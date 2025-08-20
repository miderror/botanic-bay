# backend/app/models/cart.py
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.logger import logger
from app.models.base import Base


class CartItem(Base):
    """
    Модель элемента корзины
    Хранит информацию о конкретном товаре в корзине
    """

    __tablename__ = "cart_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cart_id = Column(UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"))
    product_id = Column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE")
    )
    quantity = Column(Integer, nullable=False)

    # Связи с другими таблицами
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

    @property
    def price(self) -> Decimal:
        """Цена товара"""
        return self.product.price if self.product else Decimal("0")

    @property
    def subtotal(self) -> Decimal:
        """Стоимость позиции"""
        return self.price * self.quantity

    @property
    def product_name(self) -> str:
        """Название товара"""
        return self.product.name if self.product else ""

    @property
    def image_url(self) -> Optional[str]:
        """URL изображения товара"""
        return self.product.image_url if self.product else None


class Cart(Base):
    """
    Модель корзины пользователя
    Хранит информацию о товарах в корзине и времени её действия
    """

    __tablename__ = "carts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Связи с другими таблицами
    items = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )
    user = relationship("User", backref="carts")

    @property
    def total(self) -> Decimal:
        """Общая стоимость корзины"""
        return sum(item.subtotal for item in self.items)

    def to_schema(self) -> "SCart":
        """
        Преобразование в формат схемы SCart

        Returns:
            SCart: Данные корзины в формате схемы
        """
        from app.schemas.cart import SCart, SCartItem

        items = []
        if hasattr(self, "items"):  # Проверяем, что items предзагружены
            for item in self.items:
                if hasattr(item, "product"):  # Проверяем, что product предзагружен
                    items.append(
                        SCartItem(
                            id=item.id,
                            product_id=item.product_id,
                            quantity=item.quantity,
                            price=item.price,
                            subtotal=item.subtotal,
                            product_name=item.product_name,
                            image_url=item.product.image_url,
                        )
                    )

        return SCart(
            id=self.id,
            items=items,
            total=self.total,
            expires_at=self.expires_at,
            is_active=self.is_active,
        )

    def is_expired(self) -> bool:
        """Проверка истекла ли корзина"""
        return datetime.now().astimezone() > self.expires_at

    def get_total_price(self) -> float:
        """
        Расчет общей стоимости товаров в корзине

        Returns:
            float: Общая стоимость
        """
        total = sum(item.product.price * item.quantity for item in self.items)
        logger.debug(
            "Calculated cart total price",
            extra={"cart_id": str(self.id), "total_price": str(total)},
        )
        return float(total)

    def add_item(self, product_id: UUID, quantity: int) -> Optional[CartItem]:
        """
        Добавление товара в корзину

        Args:
            product_id: ID товара
            quantity: Количество

        Returns:
            Optional[CartItem]: Созданный элемент корзины
        """
        # Проверяем есть ли уже такой товар
        existing_item = next(
            (item for item in self.items if item.product_id == product_id), None
        )

        if existing_item:
            existing_item.quantity += quantity
            logger.debug(
                "Updated cart item quantity",
                extra={
                    "cart_id": str(self.id),
                    "product_id": str(product_id),
                    "new_quantity": existing_item.quantity,
                },
            )
            return existing_item

        # Создаем новый элемент
        cart_item = CartItem(cart_id=self.id, product_id=product_id, quantity=quantity)
        self.items.append(cart_item)

        logger.debug(
            "Added new item to cart",
            extra={
                "cart_id": str(self.id),
                "product_id": str(product_id),
                "quantity": quantity,
            },
        )
        return cart_item

    def remove_item(self, product_id: UUID) -> bool:
        """
        Удаление товара из корзины

        Args:
            product_id: ID товара

        Returns:
            bool: True если товар был удален
        """
        initial_count = len(self.items)
        self.items = [item for item in self.items if item.product_id != product_id]

        was_removed = len(self.items) < initial_count
        if was_removed:
            logger.debug(
                "Removed item from cart",
                extra={"cart_id": str(self.id), "product_id": str(product_id)},
            )

        return was_removed

    def clear(self) -> None:
        """Очистка корзины"""
        self.items = []
        logger.debug("Cleared cart", extra={"cart_id": str(self.id)})
