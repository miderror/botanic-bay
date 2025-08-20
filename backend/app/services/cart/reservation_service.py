# backend/app/services/cart/reservation_service.py
from typing import Dict, Optional
from uuid import UUID

from app.core.logger import logger
from app.crud.product import ProductCRUD


class ReservationService:
    """Сервис для управления резервацией товаров"""

    def __init__(self, product_crud: ProductCRUD):
        self.product_crud = product_crud
        self._reservations: Dict[UUID, Dict[UUID, int]] = (
            {}
        )  # product_id -> {cart_id: quantity}

    async def get_available_quantity(
        self, product_id: UUID, exclude_cart_id: Optional[UUID] = None
    ) -> int:
        """
        Получение доступного количества товара с учетом резерваций

        Args:
            product_id: ID товара
            exclude_cart_id: ID корзины, которую нужно исключить из подсчета

        Returns:
            int: Доступное количество
        """
        product = await self.product_crud.get_product(product_id)
        if not product:
            return 0

        # Считаем общее количество резерваций
        reserved = sum(
            quantity
            for cart_id, quantity in self._reservations.get(product_id, {}).items()
            if cart_id != exclude_cart_id
        )

        return max(0, product.stock - reserved)

    async def reserve_product(
        self, product_id: UUID, quantity: int, cart_id: UUID
    ) -> bool:
        """
        Резервация товара

        Args:
            product_id: ID товара
            quantity: Количество для резервации
            cart_id: ID корзины

        Returns:
            bool: True если резервация успешна
        """
        if product_id not in self._reservations:
            self._reservations[product_id] = {}

        self._reservations[product_id][cart_id] = quantity

        logger.debug(
            "Reserved product quantity",
            extra={
                "product_id": str(product_id),
                "cart_id": str(cart_id),
                "quantity": quantity,
            },
        )

        return True

    async def update_reservation(
        self, product_id: UUID, quantity: int, cart_id: UUID
    ) -> bool:
        """
        Обновление резервации

        Args:
            product_id: ID товара
            quantity: Новое количество
            cart_id: ID корзины

        Returns:
            bool: True если обновление успешно
        """
        if product_id not in self._reservations:
            return await self.reserve_product(product_id, quantity, cart_id)

        self._reservations[product_id][cart_id] = quantity

        logger.debug(
            "Updated product reservation",
            extra={
                "product_id": str(product_id),
                "cart_id": str(cart_id),
                "quantity": quantity,
            },
        )

        return True

    async def remove_reservation(self, product_id: UUID, cart_id: UUID) -> None:
        """
        Удаление резервации

        Args:
            product_id: ID товара
            cart_id: ID корзины
        """
        if product_id in self._reservations:
            self._reservations[product_id].pop(cart_id, None)

            logger.debug(
                "Removed product reservation",
                extra={"product_id": str(product_id), "cart_id": str(cart_id)},
            )

    async def remove_all_reservations(self, cart_id: UUID) -> None:
        """
        Удаление всех резерваций для корзины

        Args:
            cart_id: ID корзины
        """
        for product_reservations in self._reservations.values():
            product_reservations.pop(cart_id, None)

        logger.debug(
            "Removed all reservations for cart", extra={"cart_id": str(cart_id)}
        )
