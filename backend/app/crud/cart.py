# backend/app/crud/cart.py
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.logger import logger
from app.core.settings import settings
from app.models.cart import Cart, CartItem


class CartCRUD:
    """CRUD операции для работы с корзиной"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def deactivate_if_empty(self, cart_id: UUID) -> bool:
        """
        Деактивация корзины, если она пуста

        Args:
            cart_id: ID корзины

        Returns:
            bool: True если корзина была деактивирована
        """
        cart = await self.get_cart_by_id(cart_id)
        if not cart or cart.items:
            return False

        cart.is_active = False
        await self.session.commit()

        logger.info("Deactivated empty cart", extra={"cart_id": str(cart_id)})

        return True

    async def get_active_cart(self, user_id: UUID) -> Optional[Cart]:
        """
        Получение активной корзины пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Cart]: Активная корзина или None
        """
        query = (
            select(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.product))
            .where(
                and_(
                    Cart.user_id == user_id,
                    Cart.is_active == True,
                    Cart.expires_at > datetime.now().astimezone(),
                )
            )
            .order_by(
                Cart.created_at.desc()
            )  # Добавляем сортировку по дате создания (от новых к старым)
            .limit(1)  # Добавляем лимит, чтобы получить только одну запись
        )
        result = await self.session.execute(query)
        cart = result.unique().scalar_one_or_none()

        if cart:
            logger.debug(
                "Retrieved active cart",
                extra={"cart_id": str(cart.id), "user_id": str(user_id)},
            )

        return cart

    async def deactivate_other_carts(self, user_id: UUID, current_cart_id: UUID) -> int:
        """
        Деактивирует все другие активные корзины пользователя, кроме текущей

        Args:
            user_id: ID пользователя
            current_cart_id: ID текущей корзины, которую нужно оставить активной

        Returns:
            int: Количество деактивированных корзин
        """
        stmt = (
            update(Cart)
            .where(
                and_(
                    Cart.user_id == user_id,
                    Cart.is_active == True,
                    Cart.id != current_cart_id,
                )
            )
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()

        count = result.rowcount
        if count > 0:
            logger.info(
                f"Deactivated {count} other active carts",
                extra={
                    "user_id": str(user_id),
                    "current_cart_id": str(current_cart_id),
                    "deactivated_count": count,
                },
            )

        return count

    async def create_cart(self, user_id: UUID) -> Cart:
        """
        Создание новой корзины

        Args:
            user_id: ID пользователя

        Returns:
            Cart: Созданная корзина
        """
        # Создаем корзину с временем жизни из настроек
        expires_at = datetime.now().astimezone() + timedelta(
            minutes=settings.CART_LIFETIME_MINUTES
        )

        cart = Cart(user_id=user_id, expires_at=expires_at, is_active=True)

        self.session.add(cart)
        await self.session.commit()

        # Деактивируем другие корзины пользователя
        await self.deactivate_other_carts(user_id, cart.id)

        # Получаем корзину со всеми связями после создания
        cart = await self.get_cart_by_id(cart.id)

        logger.info(
            "Created new cart",
            extra={
                "cart_id": str(cart.id),
                "user_id": str(user_id),
                "expires_at": expires_at.isoformat(),
            },
        )

        return cart

    async def add_product(
        self, cart_id: UUID, product_id: UUID, quantity: int
    ) -> Optional[Cart]:  # Изменяем возвращаемый тип на Cart
        """
        Добавление товара в корзину

        Args:
            cart_id: ID корзины
            product_id: ID товара
            quantity: Количество

        Returns:
            Optional[Cart]: Обновленная корзина или None
        """
        # Получаем корзину с предзагрузкой связей
        cart = await self.get_cart_by_id(cart_id)
        if not cart or not cart.is_active or cart.is_expired():
            logger.warning(
                "Cannot add to cart - cart is inactive or expired",
                extra={"cart_id": str(cart_id)},
            )
            return None

        # Создаем или обновляем элемент корзины
        cart_item = cart.add_item(product_id, quantity)
        if cart_item:
            await self.session.commit()

            # Заново получаем корзину со всеми связями
            cart = await self.get_cart_by_id(cart_id)

        return cart

    async def update_quantity(
        self, cart_id: UUID, product_id: UUID, quantity: int
    ) -> Optional[CartItem]:
        """
        Обновление количества товара в корзине

        Args:
            cart_id: ID корзины
            product_id: ID товара
            quantity: Новое количество

        Returns:
            Optional[CartItem]: Обновленный элемент корзины
        """
        query = select(CartItem).where(
            and_(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        )
        result = await self.session.execute(query)
        cart_item = result.scalar_one_or_none()

        if cart_item:
            cart_item.quantity = quantity
            await self.session.commit()
            await self.session.refresh(cart_item)

            logger.debug(
                "Updated cart item quantity",
                extra={
                    "cart_id": str(cart_id),
                    "product_id": str(product_id),
                    "quantity": quantity,
                },
            )

        return cart_item

    async def remove_product(self, cart_id: UUID, product_id: UUID) -> bool:
        """
        Удаление товара из корзины

        Args:
            cart_id: ID корзины
            product_id: ID товара

        Returns:
            bool: True если товар был удален
        """
        cart = await self.get_cart_by_id(cart_id)
        if not cart:
            return False

        if cart.remove_item(product_id):
            await self.session.commit()
            return True

        return False

    async def clear_cart(self, cart_id: UUID) -> bool:
        """
        Очистка корзины

        Args:
            cart_id: ID корзины

        Returns:
            bool: True если корзина была очищена
        """
        cart = await self.get_cart_by_id(cart_id)
        if not cart:
            return False

        cart.clear()
        await self.session.commit()
        return True

    async def extend_expiration(
        self, cart_id: UUID, minutes: int = 60
    ) -> Optional[Cart]:
        """
        Продление времени жизни корзины

        Args:
            cart_id: ID корзины
            minutes: Количество минут для продления

        Returns:
            Optional[Cart]: Обновленная корзина
        """
        cart = await self.get_cart_by_id(cart_id)
        if not cart:
            return None

        cart.expires_at = datetime.now().astimezone() + timedelta(minutes=minutes)
        await self.session.commit()
        await self.session.refresh(cart)

        logger.info(
            "Extended cart expiration",
            extra={
                "cart_id": str(cart_id),
                "new_expires_at": cart.expires_at.isoformat(),
            },
        )

        return cart

    async def deactivate_cart(self, cart_id: UUID) -> bool:
        """
        Деактивация корзины

        Args:
            cart_id: ID корзины

        Returns:
            bool: True если корзина была деактивирована
        """
        cart = await self.get_cart_by_id(cart_id)
        if not cart:
            return False

        cart.is_active = False
        await self.session.commit()

        logger.info("Deactivated cart", extra={"cart_id": str(cart_id)})

        return True

    async def get_expired_carts(self) -> List[Cart]:
        """
        Получение списка просроченных корзин

        Returns:
            List[Cart]: Список просроченных корзин
        """
        query = select(Cart).where(
            and_(Cart.is_active == True, Cart.expires_at <= datetime.now().astimezone())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_cart_by_id(self, cart_id: UUID) -> Optional[Cart]:
        """
        Получение корзины по ID с предзагрузкой связанных данных

        Args:
            cart_id: ID корзины

        Returns:
            Optional[Cart]: Найденная корзина или None
        """
        query = (
            select(Cart)
            .options(joinedload(Cart.items).joinedload(CartItem.product))
            .where(Cart.id == cart_id)
        )
        result = await self.session.execute(query)
        cart = result.unique().scalar_one_or_none()

        if cart:
            logger.debug("Retrieved cart by id", extra={"cart_id": str(cart_id)})

        return cart

    async def get_active_carts_with_product(self, product_id: UUID) -> List[Cart]:
        """
        Получение активных корзин, содержащих указанный товар

        Args:
            product_id: ID товара

        Returns:
            List[Cart]: Список активных корзин с товаром
        """
        query = (
            select(Cart)
            .options(joinedload(Cart.items))
            .where(
                and_(
                    Cart.is_active == True,
                    Cart.expires_at > datetime.now().astimezone(),
                    Cart.items.any(CartItem.product_id == product_id),
                )
            )
        )

        result = await self.session.execute(query)
        return result.unique().scalars().all()  # Добавили unique()

    async def cleanup_duplicate_carts(self) -> int:
        """
        Очищает дублирующиеся активные корзины, оставляя только самую свежую для каждого пользователя

        Returns:
            int: Количество деактивированных дублирующихся корзин
        """
        # Сначала получаем список пользователей с несколькими активными корзинами
        users_query = (
            select(Cart.user_id)
            .where(Cart.is_active == True)
            .group_by(Cart.user_id)
            .having(func.count() > 1)
        )
        result = await self.session.execute(users_query)
        users_with_multiple_carts = result.scalars().all()

        total_deactivated = 0
        for user_id in users_with_multiple_carts:
            # Для каждого пользователя находим его самую свежую корзину
            latest_cart_query = (
                select(Cart.id)
                .where(and_(Cart.user_id == user_id, Cart.is_active == True))
                .order_by(Cart.created_at.desc())
                .limit(1)
            )
            latest_result = await self.session.execute(latest_cart_query)
            latest_cart_id = latest_result.scalar_one()

            # Деактивируем все остальные корзины пользователя
            count = await self.deactivate_other_carts(user_id, latest_cart_id)
            total_deactivated += count

        return total_deactivated
