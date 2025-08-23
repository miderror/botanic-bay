# backend/app/models/order.py
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.logger import logger
from app.models.base import Base
from app.models.order_status import OrderStatus
from app.models.cart import Cart
from app.schemas.cdek.base import RequestLocation


class OrderItem(Base):
    """
    Модель элемента заказа
    Хранит информацию о конкретном товаре в заказе, включая цену на момент заказа
    """

    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE")
    )
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # Цена на момент заказа

    # Связи с другими таблицами
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

    def get_last_payment(self):
        """
        Получение последнего созданного платежа для заказа

        Returns:
            Optional[Payment]: Последний платеж или None
        """
        if not self.payments:
            return None
        return sorted(self.payments, key=lambda p: p.created_at, reverse=True)[0]

    @property
    def subtotal(self) -> float:
        """Подсчет стоимости позиции"""
        return float(self.price * self.quantity)

    @property
    def product_name(self) -> str:
        """Название товара"""
        return self.product.name if self.product else ""

    @property
    def image_url(self) -> Optional[str]:
        """URL изображения товара"""
        return self.product.image_url if self.product else None


class Order(Base):
    """
    Модель заказа
    Хранит информацию о заказе пользователя
    """

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(String(20), nullable=False, default=OrderStatus.PENDING.value)

    # Информация о доставке
    delivery_method = Column(String(50), nullable=False)
    delivery_warehouse_address = Column(Text, nullable=True)
    delivery_point = Column(String(15), nullable=True)
    delivery_to_location = Column(JSONB, nullable=True)
    delivery_comment = Column(String, nullable=True)
    delivery_tariff_code = Column(Integer, nullable=False)

    delivery_cost = Column(Numeric(10, 2), nullable=False)
    delivery_data = Column(JSONB, nullable=True)  # Дополнительные данные о доставке

    # Информация об оплате
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(String(20), nullable=True)
    payment_data = Column(JSONB, nullable=True)  # Данные об оплате

    # Стоимость
    subtotal = Column(Numeric(10, 2), nullable=False)  # Стоимость товаров
    discount_amount = Column(Numeric(10, 2), default=0)
    promo_code = Column(String(50), nullable=True)
    total = Column(Numeric(10, 2), nullable=False)  # Полная стоимость с доставкой

    # Дата планируемой отгрузки
    planned_shipping_date = Column(DateTime(timezone=True), nullable=True)

    # Связи с другими таблицами
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    user = relationship("User", backref="orders")

    payments = relationship(
        "Payment", back_populates="order", cascade="all, delete-orphan"
    )

    def calculate_totals(self, discount_multiplier: Decimal, promo_discount: Decimal = Decimal("0")) -> None:
        """
        Пересчет общей стоимости заказа
        Учитывает стоимость товаров и доставки
        """
        # Сбрасываем и заново считаем subtotal
        self.subtotal = 0

        # Логирование для отладки
        item_details = []
        for item in self.items:
            # Используем свойство subtotal из класса OrderItem
            item_detail = {
                "product_id": str(item.product_id),
                "quantity": item.quantity,
                "price": float(item.price),
                "subtotal_property": item.subtotal,
            }
            # ВАЖНО: самостоятельно считаем subtotal для отладки
            manual_subtotal = float(item.price) * item.quantity
            item_detail["manual_subtotal"] = manual_subtotal

            # Добавляем к общей сумме используя ТОЛЬКО одну из формул
            self.subtotal += manual_subtotal

            item_details.append(item_detail)

        # Считаем общую сумму с доставкой
        self.subtotal *= float(discount_multiplier)
        self.discount_amount = float(promo_discount)
        self.total = float(self.subtotal or 0) - float(self.discount_amount or 0) + float(self.delivery_cost or 0)

        # Подробное логирование
        logger.info(
            "Order totals calculation",
            extra={
                "order_id": str(self.id),
                "item_count": len(self.items),  # Сколько элементов обрабатываем
                "item_details": item_details,
                "calculated_subtotal": float(self.subtotal),
                "delivery_cost": float(self.delivery_cost),
                "total": float(self.total),
            },
        )

    @classmethod
    def from_cart(
        cls,
        cart: Cart,
        delivery_method: str,
        delivery_cost: float,
        delivery_tariff_code: int,
        *,
        discount_multiplier: Decimal = Decimal("1"),
        promo_discount: Decimal = Decimal("0"),
        delivery_point: str = None,
        delivery_to_location: RequestLocation = None,
        delivery_comment: Optional[str] = None,
    ) -> "Order":
        """
        Создание заказа из корзины

        Args:
            cart: Корзина пользователя
            delivery_method: Метод доставки
            delivery_tariff_code: Код тарифа для доставки
            delivery_cost: Стоимость доставки
            discount_multiplier: Коэффициент персональной скидки пользователя
            delivery_point: Код ПВЗ СДЕК
            delivery_to_location: Объект, описывающий локацию доставки (Курьер)
            delivery_comment: Комментарий к доставке (Курьер - указываем доп. инфу)

        Returns:
            Order: Созданный заказ
        """
        logger.info(
            "Starting order creation from cart",
            extra={
                "cart_id": str(cart.id),
                "cart_total": str(cart.total),
                "cart_items": [
                    (
                        item.product_id,
                        item.quantity,
                        float(item.price),
                        float(item.subtotal),
                    )
                    for item in cart.items
                ],
            },
        )

        if delivery_to_location:
            delivery_to_location = delivery_to_location.model_dump(
                exclude_unset=True,
                exclude_none=True,
            )

        order = cls(
            user_id=cart.user_id,
            delivery_point=delivery_point,
            delivery_to_location=delivery_to_location,
            delivery_method=delivery_method,
            delivery_cost=delivery_cost,
            delivery_comment=delivery_comment,
            status=OrderStatus.PENDING.value,
            delivery_tariff_code=delivery_tariff_code,
        )

        # Создаем элементы заказа из корзины
        for cart_item in cart.items:
            price = float(cart_item.product.price)
            quantity = cart_item.quantity

            logger.info(
                "Creating order item",
                extra={
                    "product_id": str(cart_item.product_id),
                    "quantity": quantity,
                    "price": price,
                    "expected_subtotal": price * quantity,
                },
            )

            # Создаем элемент заказа без привязки к order во избежание дублирования
            order_item = OrderItem(
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price,  # Фиксируем текущую цену
            )

            # Явно добавляем его в список элементов заказа
            order.items.append(order_item)

        # Рассчитываем итоговую стоимость
        order.calculate_totals(discount_multiplier, promo_discount)

        logger.info(
            "Completed order creation",
            extra={
                "order_id": str(order.id),
                "items_count": len(order.items),
                "subtotal": float(order.subtotal),
                "total": float(order.total),
            },
        )

        # Определяем планируемую дату отгрузки
        now = datetime.now().astimezone()
        if now.hour < 15:  # До 15:00
            order.planned_shipping_date = now.replace(
                hour=15, minute=0, second=0, microsecond=0
            )
        else:  # После 15:00 - отгрузка на следующий день
            tomorrow = now + timedelta(days=1)
            order.planned_shipping_date = tomorrow.replace(
                hour=15, minute=0, second=0, microsecond=0
            )

        logger.info(
            "Created order from cart",
            extra={
                "order_id": str(order.id),
                "cart_id": str(cart.id),
                "user_id": str(cart.user_id),
                "planned_shipping_date": order.planned_shipping_date.isoformat(),
            },
        )

        return order

    def update_status(
        self, new_status: str, payment_status: Optional[str] = None
    ) -> None:
        """
        Обновление статуса заказа

        Args:
            new_status: Новый статус заказа
            payment_status: Новый статус оплаты (опционально)
        """
        if new_status not in OrderStatus.get_all_statuses():
            raise ValueError(f"Invalid order status: {new_status}")

        old_status = self.status
        self.status = new_status

        # Обновляем статус оплаты, если он передан
        if payment_status is not None:
            old_payment_status = self.payment_status
            self.payment_status = payment_status

            logger.info(
                "Updated order payment status",
                extra={
                    "order_id": str(self.id),
                    "old_payment_status": old_payment_status,
                    "new_payment_status": payment_status,
                },
            )

        logger.info(
            "Updated order status",
            extra={
                "order_id": str(self.id),
                "old_status": old_status,
                "new_status": new_status,
            },
        )
