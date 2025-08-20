# backend/app/api/v1/endpoints/cart.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.core.logger import logger
from app.crud.cart import CartCRUD
from app.crud.product import ProductCRUD
from app.models.user import User
from app.schemas.cart import SAddToCart, SCartResponse, SUpdateCartItem
from app.services.cart.cart_service import CartService

router = APIRouter()


async def get_cart_service(session: AsyncSession = Depends(get_session)) -> CartService:
    """Получение сервиса для работы с корзиной"""
    cart_crud = CartCRUD(session)
    product_crud = ProductCRUD(session)
    return CartService(cart_crud, product_crud)


@router.get("/my", response_model=SCartResponse)
async def get_my_cart(
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service),
):
    """
    Получение текущей корзины пользователя
    """
    try:
        cart = await cart_service.get_or_create_cart(current_user.id)

        # Преобразуем корзину в схему
        cart_schema = cart.to_schema() if cart else None

        return SCartResponse(cart=cart_schema, message="Cart retrieved successfully")
    except Exception as e:
        logger.error(
            "Failed to get user cart",
            extra={"user_id": str(current_user.id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cart",
        )


@router.post("/add", response_model=SCartResponse)
async def add_to_cart(
    data: SAddToCart,
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service),
):
    """Добавление товара в корзину"""
    try:
        cart = await cart_service.add_to_cart(current_user.id, data)
        return SCartResponse(
            cart=cart.to_schema(),  # Используем метод to_schema()
            message="Product added to cart successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to add product to cart",
            extra={"user_id": str(current_user.id), "product_id": str(data.product_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add product to cart",
        )


# TODO: Аналогично обновляем остальные эндпоинты, использующие SCartResponse


@router.patch("/{product_id}", response_model=SCartResponse)
async def update_cart_item(
    product_id: UUID,
    data: SUpdateCartItem,
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service),
):
    """
    Обновление количества товара в корзине
    """
    try:
        cart = await cart_service.update_quantity(current_user.id, product_id, data)
        return SCartResponse(cart=cart, message="Cart item updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update cart item",
            extra={"user_id": str(current_user.id), "product_id": str(product_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cart item",
        )


@router.delete("/{product_id}", response_model=SCartResponse)
async def remove_from_cart(
    product_id: UUID,
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service),
):
    """
    Удаление товара из корзины
    """
    try:
        cart = await cart_service.remove_from_cart(current_user.id, product_id)
        return SCartResponse(
            cart=cart, message="Product removed from cart successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to remove product from cart",
            extra={"user_id": str(current_user.id), "product_id": str(product_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove product from cart",
        )


@router.delete("/", response_model=SCartResponse)
@router.delete("", response_model=SCartResponse)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service),
):
    """
    Очистка корзины
    """
    try:
        await cart_service.clear_cart(current_user.id)
        return SCartResponse(cart=None, message="Cart cleared successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to clear cart",
            extra={"user_id": str(current_user.id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart",
        )
