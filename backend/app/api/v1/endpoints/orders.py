"""Содержит эндпоинты для работы с заказами, адресами пользователей и пунктами доставки."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_cdek_service,
    get_current_admin,
    get_current_user,
    get_discount_service,
)
from app.core.db import get_session
from app.core.logger import logger
from app.crud.cart import CartCRUD
from app.crud.cdek_delivery_point import CDEKDeliveryPointCRUD
from app.crud.order import OrderCRUD
from app.crud.user_address import UserAddressCRUD
from app.crud.user_delivery_point import UserDeliveryPointCRUD
from app.models.order_status import OrderStatus
from app.models.user import User
from app.schemas.cdek.response import SDeliveryPoint
from app.schemas.order import (
    SCreateOrder,
    SOrder,
    SOrderFilter,
    SOrderList,
    SUpdateOrderStatus,
    SUserAddress,
    SUserDeliveryPoint,
)
from app.services.cdek.cdek_service import CDEKService
from app.services.order.discount_service import DiscountService
from app.services.order.order_service import OrderService

router = APIRouter()


# MARK: Orders
async def get_order_service(
    session: AsyncSession = Depends(get_session),
    cdek_service: CDEKService = Depends(get_cdek_service),
    discount_service: DiscountService = Depends(get_discount_service),
) -> OrderService:
    """Получение сервиса для работы с заказами"""
    order_crud = OrderCRUD(session)
    cart_crud = CartCRUD(session)

    cdek_delivery_point_crud = CDEKDeliveryPointCRUD(session)
    user_address_crud = UserAddressCRUD(session)
    user_delivery_point_crud = UserDeliveryPointCRUD(session)

    return OrderService(
        order_crud,
        cart_crud,
        cdek_delivery_point_crud,
        user_address_crud,
        user_delivery_point_crud,
        cdek_service,
        discount_service,
        session,
    )


@router.post("", response_model=SOrder)
async def create_order(
    data: SCreateOrder,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Создание заказа из текущей корзины пользователя
    """
    try:
        # Создаем заказ
        order = await order_service.create_order(current_user.id, data)

        # Получаем заказ со всеми связями для корректной сериализации
        order = await order_service.get_order_details(order.id)

        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create order",
            extra={"user_id": str(current_user.id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order",
        )


@router.patch("/{order_id}/cancel", response_model=SOrder)
async def cancel_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Отмена заказа пользователем
    """
    try:
        order = await order_service.cancel_order(order_id, current_user.id)
        return order
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(
            "Failed to cancel order",
            extra={
                "order_id": str(order_id),
                "user_id": str(current_user.id),
                "error": str(e),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order",
        )


@router.get("/my", response_model=SOrderList)
async def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    order_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Получение списка заказов текущего пользователя
    """
    try:
        orders, total = await order_service.get_user_orders(
            current_user.id, skip=skip, limit=limit, status=order_status
        )

        return SOrderList(
            items=orders,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit,
        )
    except Exception as e:
        logger.error(
            "Failed to get user orders",
            extra={"user_id": str(current_user.id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders",
        )


@router.get("/my/{order_id}", response_model=SOrder)
async def get_my_order_details(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Получение деталей конкретного заказа пользователя
    """
    try:
        return await order_service.get_order_details(order_id, user_id=current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get order details",
            extra={"order_id": str(order_id), "user_id": str(current_user.id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order details",
        )


@router.patch("/my/{order_id}/cancel", response_model=SOrder)
async def cancel_my_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Отмена заказа пользователем
    """
    try:
        return await order_service.update_order_status(
            order_id, SUpdateOrderStatus(status=OrderStatus.CANCELLED.value)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to cancel order",
            extra={"order_id": str(order_id), "user_id": str(current_user.id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order",
        )


# MARK: Admin
@router.get("/admin", response_model=SOrderList)
async def get_orders_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    filters: Optional[SOrderFilter] = None,
    _: User = Depends(get_current_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Получение списка всех заказов (для администраторов)
    """
    try:
        orders, total = await order_service.get_orders_for_admin(
            skip=skip, limit=limit, filters=filters
        )

        return SOrderList(
            items=orders,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit,
        )
    except Exception as e:
        logger.error("Failed to get orders for admin", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders",
        )


@router.get("/admin/{order_id}", response_model=SOrder)
async def get_order_details_admin(
    order_id: UUID,
    _: User = Depends(get_current_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Получение деталей заказа (для администраторов)
    """
    try:
        return await order_service.get_order_details(order_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get order details for admin",
            extra={"order_id": str(order_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order details",
        )


@router.patch("/admin/{order_id}/status", response_model=SOrder)
async def update_order_status_admin(
    order_id: UUID,
    data: SUpdateOrderStatus,
    _: User = Depends(get_current_admin),
    order_service: OrderService = Depends(get_order_service),
):
    """
    Обновление статуса заказа (для администраторов)
    """
    try:
        return await order_service.update_order_status(order_id, data, admin=True)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update order status",
            extra={"order_id": str(order_id), "new_status": data.status},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status",
        )


# MARK: Delivery Points
@router.get("/delivery_points", response_model=list[SUserDeliveryPoint])
async def get_my_delivery_points(
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    user_id = current_user.id
    try:
        return await order_service.get_user_delivery_points(current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch user delivery points",
            extra={"user_id": str(user_id), "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user delivery points",
        )


@router.delete("/delivery_points/{point_id}")
async def delete_user_delivery_point(
    point_id: UUID,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    user_id = current_user.id
    try:
        return await order_service.delete_user_delivery_point(point_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to save delete user delivery point",
            extra={
                "user_id": str(user_id),
                "error": str(e),
                "point_id": str(point_id),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save delete user delivery point",
        )


@router.post("/delivery_points", response_model=SUserDeliveryPoint)
async def save_user_delivery_point(
    data: SDeliveryPoint,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    user_id = current_user.id
    try:
        return await order_service.save_user_delivery_point(current_user, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to save user delivery point",
            extra={
                "user_id": str(user_id),
                "error": str(e),
                "delivery_point": str(data.model_dump_json()),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# MARK: User Addresses
@router.post("/addresses", response_model=SUserAddress)
async def save_user_address(
    data: SUserAddress,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    user_id = current_user.id
    try:
        return await order_service.save_user_address(current_user, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to save user addresses",
            extra={
                "user_id": str(user_id),
                "error": str(e),
                "user_address": str(data.model_dump_json()),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/addresses", response_model=list[SUserAddress])
async def get_my_addresses(
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    user_id = current_user.id
    try:
        return await order_service.get_user_addresses(current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch user addresses",
            extra={"user_id": str(user_id), "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user addresses",
        )


@router.patch("/addresses/{address_id}", response_model=SUserAddress)
async def update_user_address(
    address_id: UUID,
    data: SUserAddress,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """Обновляет дополнительные поля существующего адреса пользователя.
    Адрес должен принадлежать текущему пользователю."""
    user_id = current_user.id
    try:
        return await order_service.update_user_address(
            user_id=user_id,
            address_id=address_id,
            user_address=data,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update user address",
            extra={
                "user_id": str(user_id),
                "address_id": str(address_id),
                "error": str(e),
                "user_address": str(data.model_dump_json()),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/addresses/{address_id}")
async def delete_user_address(
    address_id: UUID,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    user_id = current_user.id
    try:
        return await order_service.delete_user_address(address_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to save delete user address",
            extra={
                "user_id": str(user_id),
                "error": str(e),
                "user_address_id": str(address_id),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save delete user address",
        )
