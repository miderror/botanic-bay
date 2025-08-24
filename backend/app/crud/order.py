# backend/app/crud/order.py
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.logger import logger
from app.models import Order
from app.models.cart import Cart
from app.models.order import Order, OrderItem
from app.models.order_status import OrderStatus
from app.schemas.cdek.base import RequestLocation


class OrderCRUD:
    """CRUD операции для работы с заказами"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_from_cart(
        self,
        cart: Cart,
        delivery_method: str,
        delivery_cost: float,
        payment_method: str,
        delivery_tariff_code: int,
        *,
        discount_multiplier: Decimal = Decimal("1"),
        promo_discount: Decimal = Decimal("0"),
        delivery_point: str = None,
        delivery_to_location: RequestLocation = None,
        delivery_comment: Optional[str] = None,
    ) -> Order:
        """
        Создание заказа из корзины

        Args:
            cart: Корзина пользователя
            delivery_method: Метод доставки
            delivery_cost: Стоимость доставки
            payment_method: Метод оплаты
            delivery_tariff_code: Код тарифа для доставки
            discount_multiplier: Коэффициент персональной скидки пользователя
            delivery_point: Код ПВЗ СДЕК
            delivery_to_location: Объект, описывающий локацию доставки (Курьер)
            delivery_comment: Комментарий к доставке (Курьер - указываем доп. инфу)

        Returns:
            Order: Созданный заказ

        Raises:
            ValueError: Если корзина пуста или неактивна
        """
        if not cart.is_active or cart.is_expired():
            raise ValueError("Cart is inactive or expired")

        if not cart.items:
            raise ValueError("Cart is empty")

        # Создаем заказ из корзины
        order = Order.from_cart(
            cart=cart,
            delivery_point=delivery_point,
            delivery_to_location=delivery_to_location,
            delivery_method=delivery_method,
            discount_multiplier=discount_multiplier,
            delivery_cost=delivery_cost,
            delivery_comment=delivery_comment,
            delivery_tariff_code=delivery_tariff_code,
        )

        order.calculate_totals(discount_multiplier, promo_discount)

        # Добавляем метод оплаты
        order.payment_method = payment_method
        order.payment_status = "pending"

        self.session.add(order)

        # Деактивируем корзину
        # cart.is_active = False

        await self.session.commit()
        await self.session.refresh(order)

        logger.info(
            "Created new order from cart",
            extra={
                "order_id": str(order.id),
                "cart_id": str(cart.id),
                "user_id": str(cart.user_id),
                "total": str(order.total),
            },
        )

        return order

    async def get_order(
        self, order_id: UUID, with_items: bool = True
    ) -> Optional[Order]:
        """
        Получение заказа по ID с загрузкой всех связанных данных

        Args:
            order_id: ID заказа
            with_items: Флаг, указывающий нужно ли загружать элементы заказа

        Returns:
            Optional[Order]: Найденный заказ или None если заказ не найден
        """
        # Начинаем формировать запрос с жадной загрузкой пользователя
        query = select(Order).options(
            joinedload(Order.user)  # Жадно загружаем пользователя для каждого заказа
        )

        if with_items:
            # Жадно загружаем связанные товары для каждого элемента заказа
            query = query.options(joinedload(Order.items).joinedload(OrderItem.product))

        query = query.where(Order.id == order_id)

        result = await self.session.execute(query)
        order = result.unique().scalar_one_or_none()

        if order:
            logger.debug("Retrieved order", extra={"order_id": str(order_id)})

        return order

    async def get_user_orders(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> Tuple[List[Order], int]:
        """
        Получение заказов пользователя с пагинацией

        Args:
            user_id: ID пользователя
            skip: Количество записей, которые нужно пропустить
            limit: Максимальное количество записей для возврата
            status: Опциональный фильтр по статусу заказа

        Returns:
            Tuple[List[Order], int]: Список заказов и общее количество
        """
        # Базовый запрос с жадной загрузкой пользователя и элементов заказа
        query = (
            select(Order)
            .where(Order.user_id == user_id)
            .options(
                joinedload(Order.items).joinedload(
                    OrderItem.product
                ),  # Жадно загружаем товары
                joinedload(Order.user),  # Жадно загружаем данные пользователя
            )
        )

        # Добавляем фильтр по статусу
        if status:
            query = query.where(Order.status == status)

        # Получаем общее количество записей для пагинации
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        # Добавляем сортировку и пагинацию
        query = (
            query.order_by(
                desc(Order.created_at)
            )  # Сортировка по убыванию даты создания
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        orders = result.unique().scalars().all()

        logger.debug(
            "Retrieved user orders",
            extra={"user_id": str(user_id), "total": total, "status_filter": status},
        )

        return orders, total

    async def update_status(
        self, order_id: UUID, new_status: str, payment_status: Optional[str] = None
    ) -> Optional[Order]:
        """
        Обновление статуса заказа

        Args:
            order_id: ID заказа
            new_status: Новый статус
            payment_status: Новый статус оплаты (опционально)

        Returns:
            Optional[Order]: Обновленный заказ или None если заказ не найден
        """
        # Получаем заказ (с жадной загрузкой данных)
        order = await self.get_order(order_id)
        if not order:
            return None

        # Обновляем статус заказа
        order.update_status(new_status, payment_status)
        await self.session.commit()
        await self.session.refresh(order)

        return order

    async def get_orders_for_admin(
        self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Order], int]:
        """
        Получение заказов для административного интерфейса с расширенной фильтрацией

        Args:
            skip: Количество записей, которые нужно пропустить
            limit: Максимальное количество записей для возврата
            filters: Словарь с фильтрами для запроса

        Returns:
            Tuple[List[Order], int]: Список заказов и общее количество
        """
        # Базовый запрос с жадной загрузкой всех связанных данных
        query = select(Order).options(
            joinedload(Order.items).joinedload(
                OrderItem.product
            ),  # Жадно загружаем товары
            joinedload(Order.user),  # Жадно загружаем данные пользователя
        )

        # Применяем фильтры, если они есть
        if filters:
            query = self._apply_admin_filters(query, filters)

        # Получаем общее количество для пагинации
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        # Добавляем сортировку и пагинацию
        query = (
            query.order_by(
                desc(Order.created_at)
            )  # Сортировка по убыванию даты создания
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(query)
        orders = result.unique().scalars().all()

        logger.debug(
            "Retrieved orders for admin", extra={"total": total, "filters": filters}
        )

        return orders, total

    def _apply_admin_filters(self, query, filters: Dict[str, Any]):
        """
        Применение фильтров к запросу заказов для административного интерфейса

        Args:
            query: Базовый SQL запрос
            filters: Словарь с фильтрами

        Returns:
            Query: Запрос с примененными фильтрами
        """
        # Фильтрация по статусу заказа
        if status := filters.get("status"):
            query = query.where(Order.status == status)

        # Фильтрация по дате создания (от)
        if from_date := filters.get("from_date"):
            query = query.where(Order.created_at >= from_date)

        # Фильтрация по дате создания (до)
        if to_date := filters.get("to_date"):
            query = query.where(Order.created_at <= to_date)

        # Фильтрация по минимальной стоимости
        if min_total := filters.get("min_total"):
            query = query.where(Order.total >= min_total)

        # Фильтрация по максимальной стоимости
        if max_total := filters.get("max_total"):
            query = query.where(Order.total <= max_total)

        return query

    async def get_orders_for_shipping(self) -> Sequence[Order]:
        """
        Получение заказов, готовых к отправке
        Возвращает оплаченные заказы, у которых планируемая дата отгрузки
        меньше или равна текущему времени

        Returns:
            List[Order]: Список заказов, готовых к отправке
        """
        # Запрос на получение заказов для отгрузки с жадной загрузкой всех связанных данных
        query = (
            select(Order)
            .where(
                and_(
                    Order.status == OrderStatus.PAID.value,
                    Order.planned_shipping_date <= datetime.now().astimezone(),
                )
            )
            .options(
                joinedload(Order.items).joinedload(
                    OrderItem.product
                ),  # Жадно загружаем товары
                joinedload(Order.user),  # Жадно загружаем данные пользователя
            )
        )

        result = await self.session.execute(query)
        orders = result.unique().scalars().all()

        logger.debug(
            "Retrieved orders for shipping", extra={"orders_count": len(orders)}
        )

        return orders

    async def get_monthly_total(
        self,
        user_id: UUID,
        month_start: datetime | date = None,
    ) -> Decimal:
        """
        Суммирует total всех заказов user_id со статусом PAID,
        у которых created_at >= month_start.
        """
        if month_start is None:
            now = datetime.now(tz=timezone.utc)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        q = select(func.coalesce(func.sum(Order.total), 0)).where(
            Order.user_id == user_id,
            Order.status == OrderStatus.PAID,
            Order.created_at >= month_start,
        )
        res = await self.session.execute(q)
        return res.scalar_one()

    async def get_current_month_orders_count(self, user_id: UUID) -> int:
        """Считает количество оплаченных заказов пользователя за текущий календарный месяц."""
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        query = select(func.count(Order.id)).where(
            Order.user_id == user_id,
            Order.status == OrderStatus.PAID,
            Order.created_at >= start_of_month,
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def has_orders_in_range(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
        status: Optional[OrderStatus] = OrderStatus.PAID,
    ) -> bool:
        stmt = (
            select(Order)
            .where(
                and_(
                    Order.user_id == user_id,
                    Order.created_at >= start_date,
                    Order.created_at <= end_date,
                    Order.status == status,
                )
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
