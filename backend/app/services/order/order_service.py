from typing import Any, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserAddressNotFoundError, UserAddressUpdateError
from app.core.logger import logger
from app.crud.cart import CartCRUD
from app.crud.cdek_delivery_point import CDEKDeliveryPointCRUD
from app.crud.order import OrderCRUD
from app.crud.user_address import UserAddressCRUD
from app.crud.user_delivery_point import UserDeliveryPointCRUD
from app.models import CartItem, User, UserAddress
from app.models.order import Order
from app.schemas.cdek.base import RequestLocation
from app.schemas.cdek.response import SDeliveryPoint
from app.schemas.order import (
    SCreateOrder,
    SOrderFilter,
    SUpdateOrderStatus,
    SUserAddress,
    SUserDeliveryPoint,
)
from app.schemas.user import SUserMonthlyOrders
from app.services.cdek.cdek_service import CDEKService
from app.services.order.discount_service import DiscountService


class OrderService:
    """Сервис для работы с заказами"""

    def __init__(
        self,
        order_crud: OrderCRUD,
        cart_crud: CartCRUD,
        cdek_delivery_point_crud: CDEKDeliveryPointCRUD,
        user_address_crud: UserAddressCRUD,
        user_delivery_point_crud: UserDeliveryPointCRUD,
        cdek_service: CDEKService,
        discount_service: DiscountService,
        session: AsyncSession,
    ):
        self.order_crud = order_crud
        self.cart_crud = cart_crud
        self.cdek_delivery_point_crud = cdek_delivery_point_crud
        self.user_address_crud = user_address_crud
        self.user_delivery_point_crud = user_delivery_point_crud
        self.session = session
        self.discount_service = discount_service
        self.cdek_service = cdek_service

    @staticmethod
    def _get_delivery_comment(user_address: UserAddress) -> str:
        comment_data = {
            "квартира": user_address.apartment,
            "подъезд": user_address.entrance,
            "этаж": user_address.floor,
            "код домофона": user_address.intercom_code,
        }
        return ", ".join(
            [
                ": ".join([key, str(value)])
                for key, value in comment_data.items()
                if value
            ]
        ).capitalize()

    async def _get_delivery_info(
        self,
        items: list[CartItem],
        delivery_point_id: UUID = None,
        address_id: UUID = None,
    ) -> dict[str, Any]:
        delivery_info = {"delivery_cost": 0, "delivery_tariff_code": 777}

        cheapest_tariff = await self.cdek_service.calculate_cheapest_tariff(
            items,
            user_delivery_point_id=delivery_point_id,
            user_address_id=address_id,
        )
        delivery_point = await self.user_delivery_point_crud.get_or_none(
            point_id=delivery_point_id,
        )
        address = await self.user_address_crud.get_or_none(
            address_id=address_id,
        )

        print(f"point", delivery_point_id, delivery_point)
        print(f"address", address_id, address)

        if delivery_point:
            delivery_info["delivery_point"] = delivery_point.cdek_delivery_point.code

        if address:
            delivery_info["delivery_to_location"] = RequestLocation.model_validate(
                address,
                from_attributes=True,
            )
            delivery_info["delivery_comment"] = self._get_delivery_comment(address)

        if cheapest_tariff:
            delivery_info["delivery_tariff_code"] = cheapest_tariff.tariff_code
            delivery_info["delivery_cost"] = cheapest_tariff.delivery_sum

        print(delivery_info)
        return delivery_info

    async def create_order(
        self,
        user_id: UUID,
        data: SCreateOrder,
    ) -> Order:
        """
        Создание заказа из корзины пользователя

        Args:
            user_id: ID пользователя
            data: Данные для создания заказа

        Returns:
            Order: Созданный заказ

        Raises:
            HTTPException: При ошибке создания заказа
        """
        # Получаем активную корзину пользователя
        cart = await self.cart_crud.get_active_cart(user_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Active cart not found"
            )

        if not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty"
            )

        try:
            delivery_info = await self._get_delivery_info(
                delivery_point_id=data.delivery_point_id,
                address_id=data.address_id,
                items=cart.items,
            )
            discount_multiplier = await self.discount_service.get_discount_multiplier(
                user_id
            )

            # Создаем заказ
            order = await self.order_crud.create_from_cart(
                cart=cart,
                **delivery_info,
                discount_multiplier=discount_multiplier,
                delivery_method=data.delivery_method,
                payment_method=data.payment_method,
            )

            logger.info(
                "Created new order",
                extra={
                    "order_id": str(order.id),
                    "user_id": str(user_id),
                    "total": str(order.total),
                },
            )

            return order

        except Exception as e:
            logger.error(
                "Failed to create order", extra={"error": str(e)}, exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order",
            )

    async def cancel_order(self, order_id: UUID, user_id: UUID) -> Order:
        """
        Отмена заказа пользователем

        Args:
            order_id: ID заказа
            user_id: ID пользователя

        Returns:
            Order: Обновленный заказ

        Raises:
            HTTPException: Если заказ не найден или не может быть отменен
        """
        # Получаем заказ
        order = await self.order_crud.get_order(order_id)

        if not order:
            logger.warning(
                "Order not found for cancel",
                extra={"order_id": str(order_id), "user_id": str(user_id)},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        # Проверяем, принадлежит ли заказ пользователю
        if str(order.user_id) != str(user_id) and not await self.is_admin(user_id):
            logger.warning(
                "User is not authorized to cancel this order",
                extra={"order_id": str(order_id), "user_id": str(user_id)},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this order",
            )

        # Проверяем статус заказа
        if order.status not in ["pending", "processing", "created"]:
            logger.warning(
                "Cannot cancel order with status",
                extra={"order_id": str(order_id), "status": order.status},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel order with status '{order.status}'",
            )

        # Обновляем статус заказа
        updated_order = await self.order_crud.update_status(order_id, "cancelled")

        # Вместо прямого обращения к order.payments, делаем отдельный запрос
        # для получения платежей, связанных с заказом
        try:
            # Импортируем здесь, чтобы избежать циклических импортов
            from app.crud.payment import PaymentCRUD
            from app.schemas.payment import SPaymentUpdate

            # Создаем экземпляр PaymentCRUD
            payment_crud = PaymentCRUD(self.session)

            # Запрашиваем платежи по ID заказа
            payments = await payment_crud.get_order_payments(order_id)

            # Отменяем платежи в статусах, которые можно отменить
            for payment in payments:
                if payment.status not in ["succeeded", "refunded", "canceled"]:
                    try:
                        await payment_crud.update_payment(
                            payment.id, SPaymentUpdate(status="canceled")
                        )
                        logger.info(
                            "Payment cancelled due to order cancellation",
                            extra={
                                "order_id": str(order_id),
                                "payment_id": str(payment.id),
                            },
                        )
                    except Exception as e:
                        logger.error(
                            "Failed to cancel payment",
                            extra={
                                "order_id": str(order_id),
                                "payment_id": str(payment.id),
                                "error": str(e),
                            },
                        )
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение функции
            logger.error(
                "Failed to process payments cancellation",
                extra={"order_id": str(order_id), "error": str(e)},
            )

        logger.info(
            "Order cancelled successfully",
            extra={"order_id": str(order_id), "user_id": str(user_id)},
        )

        return updated_order

    async def get_user_orders(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> Tuple[List[Order], int]:
        """
        Получение заказов пользователя

        Args:
            user_id: ID пользователя
            skip: Сколько записей пропустить
            limit: Сколько записей вернуть
            status: Фильтр по статусу

        Returns:
            Tuple[List[Order], int]: Список заказов и общее количество
        """
        return await self.order_crud.get_user_orders(
            user_id=user_id, skip=skip, limit=limit, status=status
        )

    async def get_order_details(
        self,
        order_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Order:
        """
        Получение деталей заказа

        Args:
            order_id: ID заказа
            user_id: ID пользователя (для проверки доступа)

        Returns:
            Order: Заказ с деталями

        Raises:
            HTTPException: Если заказ не найден или нет доступа
        """
        order = await self.order_crud.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        # Проверяем доступ если указан user_id
        if user_id and order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        return order

    async def update_order_status(
        self,
        order_id: UUID,
        data: SUpdateOrderStatus,
        admin: bool = False,
        payment_status: Optional[str] = None,
    ) -> Order:
        """
        Обновление статуса заказа

        Args:
            order_id: ID заказа
            data: Новый статус
            admin: True если обновляется администратором
            payment_status: Новый статус оплаты (опционально)

        Returns:
            Order: Обновленный заказ

        Raises:
            HTTPException: При ошибке обновления
        """
        order = await self.order_crud.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        # Проверяем возможность обновления статуса
        if not admin and data.status not in self._get_allowed_status_transitions(
            order.status
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status transition",
            )

        updated_order = await self.order_crud.update_status(
            order_id, data.status, payment_status
        )

        logger.info(
            "Updated order status",
            extra={
                "order_id": str(order_id),
                "old_status": order.status,
                "new_status": data.status,
                "payment_status": payment_status,
                "updated_by_admin": admin,
            },
        )

        return updated_order

    async def get_orders_for_admin(
        self,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[SOrderFilter] = None,
    ) -> Tuple[List[Order], int]:
        """
        Получение заказов для админского интерфейса

        Args:
            skip: Сколько записей пропустить
            limit: Сколько записей вернуть
            filters: Фильтры для поиска

        Returns:
            Tuple[List[Order], int]: Список заказов и общее количество
        """
        filter_dict = filters.dict(exclude_none=True) if filters else None
        return await self.order_crud.get_orders_for_admin(
            skip=skip, limit=limit, filters=filter_dict
        )

    def _get_allowed_status_transitions(self, current_status: str) -> List[str]:
        """
        Получение списка разрешенных статусов для перехода

        Args:
            current_status: Текущий статус

        Returns:
            List[str]: Список разрешенных статусов
        """
        # Определяем разрешенные переходы статусов
        transitions = {
            "pending": ["cancelled"],
            "paid": ["processing", "cancelled"],
            "processing": ["shipped", "cancelled"],
            "shipped": ["delivered", "cancelled"],
            "delivered": [],  # Финальный статус
            "cancelled": [],  # Финальный статус
        }

        return transitions.get(current_status, [])

    async def process_ready_for_shipping_orders(self) -> None:
        """
        Обработка заказов, готовых к отгрузке
        Должна вызываться периодически через задачу планировщика
        """
        orders = await self.order_crud.get_orders_for_shipping()

        for order in orders:
            try:
                # TODO: Здесь должна быть интеграция со складом
                # Пока просто меняем статус
                await self.update_order_status(
                    order.id, SUpdateOrderStatus(status="shipped"), admin=True
                )

                logger.info(
                    "Processed order for shipping", extra={"order_id": str(order.id)}
                )

            except Exception as e:
                logger.error(
                    "Failed to process order for shipping",
                    extra={"order_id": str(order.id), "error": str(e)},
                    exc_info=True,
                )

    async def save_user_delivery_point(
        self,
        user: User,
        delivery_point: SDeliveryPoint,
    ) -> SUserDeliveryPoint:
        cdek_delivery_point = await self.cdek_delivery_point_crud.get_or_create(
            delivery_point,
        )
        user_delivery_point = await self.user_delivery_point_crud.create(
            user,
            cdek_delivery_point,
        )
        return SUserDeliveryPoint.model_validate(
            user_delivery_point,
            from_attributes=True,
        )

    async def get_user_delivery_points(
        self,
        user: User,
    ) -> list[Optional[SUserDeliveryPoint]]:
        return TypeAdapter(list[SUserDeliveryPoint]).validate_python(
            await self.user_delivery_point_crud.get_all(user),
            from_attributes=True,
        )

    async def delete_user_delivery_point(
        self,
        user_delivery_point_id: UUID,
    ) -> None:
        result = await self.user_delivery_point_crud.delete(
            user_delivery_point_id,
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED,
                detail="Error while removing user delivery point",
            )

    # MARK: User Address
    async def save_user_address(
        self,
        user: User,
        user_address: SUserAddress,
    ) -> SUserAddress:
        return SUserAddress.model_validate(
            await self.user_address_crud.create(user, user_address),
            from_attributes=True,
        )

    async def get_user_addresses(
        self,
        user: User,
    ) -> list[Optional[SUserAddress]]:
        return TypeAdapter(list[SUserAddress]).validate_python(
            await self.user_address_crud.get_all(user),
            from_attributes=True,
        )

    async def update_user_address(
        self,
        *,
        user_id: UUID,
        address_id: UUID,
        user_address: SUserAddress,
    ) -> SUserAddress:
        """Обновляет дополнительные поля существующего адреса пользователя.
        Проверяет, что адрес принадлежит указанному пользователю."""
        # Проверяем, что адрес принадлежит пользователю
        existing_address = await self.user_address_crud.get_or_none(
            user_id=user_id, address_id=address_id
        )
        if not existing_address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User address not found",
            )

        # Обновляем адрес пользователя
        try:
            updated_address = await self.user_address_crud.update(
                address_id=address_id,
                user_address=user_address,
            )
        except UserAddressNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e
        except UserAddressUpdateError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            ) from e

        try:
            result = SUserAddress.model_validate(updated_address, from_attributes=True)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Validation error: {e.errors()}",
            ) from e
        return result

    async def delete_user_address(
        self,
        user_address_id: UUID,
    ) -> None:
        result = await self.user_address_crud.delete(user_address_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED,
                detail="Error while removing user delivery point",
            )

    async def get_monthly_orders_amount(self, user_id: UUID) -> SUserMonthlyOrders:
        logger.info(
            "Getting monthly orders amount",
            extra={"user_id": user_id},
        )

        result = await self.order_crud.get_current_month_orders_count(user_id)
        return SUserMonthlyOrders(
            monthly_orders_amount=result,
        )
