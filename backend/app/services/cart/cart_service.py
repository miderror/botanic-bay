# backend/app/services/cart/cart_service.py
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.core.logger import logger
from app.crud.cart import CartCRUD
from app.crud.product import ProductCRUD
from app.models.cart import Cart
from app.schemas.cart import SAddToCart, SUpdateCartItem
from app.services.cart.reservation_service import ReservationService


class CartService:
    """Сервис для работы с корзиной"""

    def __init__(self, cart_crud: CartCRUD, product_crud: ProductCRUD):
        self.cart_crud = cart_crud
        self.product_crud = product_crud
        self.reservation_service = ReservationService(product_crud)

    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        """
        Получение активной корзины пользователя или создание новой

        Args:
            user_id: ID пользователя

        Returns:
            Cart: Активная корзина
        """
        # Пытаемся получить существующую активную корзину
        cart = await self.cart_crud.get_active_cart(user_id)

        # Если нет активной корзины - создаем новую
        if not cart:
            cart = await self.cart_crud.create_cart(user_id)
            logger.info(
                "Created new cart for user",
                extra={"user_id": str(user_id), "cart_id": str(cart.id)},
            )

        return cart

    async def add_to_cart(self, user_id: UUID, data: SAddToCart) -> Cart:
        """
        Добавление товара в корзину

        Args:
            user_id: ID пользователя
            data: Данные для добавления товара

        Returns:
            Cart: Обновленная корзина

        Raises:
            HTTPException: При ошибке добавления товара
        """
        # Получаем или создаем корзину
        cart = await self.get_or_create_cart(user_id)

        # Проверяем наличие товара
        product = await self.product_crud.get_product(data.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product is not available",
            )

        # Проверяем доступное количество с учетом резервов
        available_quantity = await self.reservation_service.get_available_quantity(
            product.id
        )
        if available_quantity < data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough product quantity available",
            )

        # Добавляем товар в корзину
        updated_cart = await self.cart_crud.add_product(
            cart.id, data.product_id, data.quantity
        )

        if not updated_cart:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to add product to cart",
            )

        # Резервируем товар
        await self.reservation_service.reserve_product(
            data.product_id, data.quantity, cart.id
        )

        return updated_cart

    async def update_quantity(
        self, user_id: UUID, product_id: UUID, data: SUpdateCartItem
    ) -> Cart:
        """
        Обновление количества товара в корзине

        Args:
            user_id: ID пользователя
            product_id: ID товара
            data: Новое количество

        Returns:
            Cart: Обновленная корзина

        Raises:
            HTTPException: При ошибке обновления
        """
        cart = await self.get_or_create_cart(user_id)

        # Проверяем наличие товара
        product = await self.product_crud.get_product(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        # Проверяем доступное количество
        available_quantity = await self.reservation_service.get_available_quantity(
            product_id, exclude_cart_id=cart.id
        )
        if available_quantity < data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough product quantity available",
            )

        # Обновляем количество
        cart_item = await self.cart_crud.update_quantity(
            cart.id, product_id, data.quantity
        )

        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found in cart",
            )

        # Если количество установлено в 0, удаляем товар
        if data.quantity == 0:
            return await self.remove_from_cart(user_id, product_id)

        # Обновляем резервацию
        await self.reservation_service.update_reservation(
            product_id, data.quantity, cart.id
        )

        return cart

    async def _check_and_deactivate_if_empty(self, cart: Cart) -> None:
        """
        Проверка корзины на пустоту и её деактивация при необходимости

        Args:
            cart: Корзина для проверки
        """
        if not cart.items:
            await self.cart_crud.deactivate_if_empty(cart.id)
            logger.debug(
                "Cart deactivated because it became empty",
                extra={"cart_id": str(cart.id)},
            )

    async def remove_from_cart(self, user_id: UUID, product_id: UUID) -> Cart:
        """
        Удаление товара из корзины

        Args:
            user_id: ID пользователя
            product_id: ID товара

        Returns:
            Cart: Обновленная корзина

        Raises:
            HTTPException: При ошибке удаления
        """
        cart = await self.get_or_create_cart(user_id)

        # Удаляем товар и его резервацию
        if await self.cart_crud.remove_product(cart.id, product_id):
            await self.reservation_service.remove_reservation(product_id, cart.id)
            # Проверяем не стала ли корзина пустой
            await self._check_and_deactivate_if_empty(cart)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found in cart",
            )

        return cart

    async def clear_cart(self, user_id: UUID) -> None:
        """
        Очистка корзины пользователя

        Args:
            user_id: ID пользователя

        Raises:
            HTTPException: При ошибке очистки
        """
        cart = await self.get_or_create_cart(user_id)

        # Очищаем корзину и все резервации
        if await self.cart_crud.clear_cart(cart.id):
            await self.reservation_service.remove_all_reservations(cart.id)
            # Деактивируем пустую корзину
            await self.cart_crud.deactivate_if_empty(cart.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to clear cart"
            )

    async def extend_cart(self, cart_id: UUID, minutes: int = 60) -> Cart:
        """
        Продление времени жизни корзины

        Args:
            cart_id: ID корзины
            minutes: Количество минут для продления

        Returns:
            Cart: Обновленная корзина

        Raises:
            HTTPException: При ошибке продления
        """
        cart = await self.cart_crud.extend_expiration(cart_id, minutes)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found"
            )

        return cart

    async def cleanup_expired_carts(self) -> None:
        """
        Очистка просроченных корзин
        Должна вызываться периодически через задачу планировщика
        """
        expired_carts = await self.cart_crud.get_expired_carts()

        for cart in expired_carts:
            # Удаляем все резервации для корзины
            await self.reservation_service.remove_all_reservations(cart.id)

            # Деактивируем корзину
            await self.cart_crud.deactivate_cart(cart.id)

            logger.info("Cleaned up expired cart", extra={"cart_id": str(cart.id)})

    async def get_available_quantity(
        self, product_id: UUID, exclude_cart_id: Optional[UUID] = None
    ) -> int:
        """
        Получение доступного количества товара с учетом резерваций в активных корзинах

        Args:
            product_id: ID товара
            exclude_cart_id: ID корзины, которую нужно исключить из подсчета

        Returns:
            int: Доступное количество

        Raises:
            HTTPException: Если товар не найден
        """
        # Проверяем существование товара
        product = await self.product_crud.get_product(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        # Получаем все активные корзины где есть этот товар
        active_carts = await self.cart_crud.get_active_carts_with_product(product_id)

        # Считаем общее количество зарезервированных единиц товара
        reserved_quantity = sum(
            cart_item.quantity
            for cart in active_carts
            for cart_item in cart.items
            if cart_item.product_id == product_id
            and cart.id != exclude_cart_id  # Исключаем указанную корзину
            and not cart.is_expired()  # Проверяем что корзина не просрочена
        )

        available = max(0, product.stock - reserved_quantity)

        logger.debug(
            "Calculated available quantity",
            extra={
                "product_id": str(product_id),
                "total_stock": product.stock,
                "reserved": reserved_quantity,
                "available": available,
            },
        )

        return available
