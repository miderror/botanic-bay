# backend/app/api/v1/endpoints/auth.py
import hashlib
import hmac
import json
from typing import Optional
from urllib.parse import unquote

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_discount_service,
    get_profile_service,
    get_referral_service,
)
from app.api.v1.endpoints.orders import get_order_service
from app.core.db import get_session
from app.core.logger import logger
from app.core.settings import settings
from app.models import User
from app.schemas.user import (
    SAuthResponse,
    SUser,
    SUserCreate,
    SUserDiscountProgress,
    SUserMonthlyOrders,
    SUserProfile,
)
from app.services.order.discount_service import DiscountService
from app.services.order.order_service import OrderService
from app.services.profile.profile_service import ProfileService
from app.services.referral.referral_service import ReferralService
from app.services.telegram.user_service import TelegramUserService

router = APIRouter()


@router.get("/discount-progress", response_model=SUserDiscountProgress)
async def get_user_discount_progress(
    current_user: User = Depends(get_current_user),
    discount_service: DiscountService = Depends(get_discount_service),
):
    try:
        return await discount_service.get_progress_to_next_level(current_user.id)
    except Exception as e:
        logger.error(
            "Failed to get user discount progress",
            extra={"user_id": current_user.id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/monthly-orders", response_model=SUserMonthlyOrders)
async def get_user_monthly_orders(
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    try:
        return await order_service.get_monthly_orders_amount(current_user.id)
    except Exception as e:
        logger.error(
            "Failed to get user monthly orders amount",
            extra={"user_id": current_user.id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/profile", response_model=SUserProfile)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    try:
        return await profile_service.get_profile(current_user.id)
    except Exception as e:
        logger.error(
            "Failed to get user profile",
            extra={"user_id": current_user.id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.patch("/profile", response_model=SUserProfile)
async def update_user_profile(
    current_user: User = Depends(get_current_user),
    data: SUserProfile = Body(...),
    profile_service: ProfileService = Depends(get_profile_service),
):
    try:
        return await profile_service.update_profile(
            current_user.id,
            **data.model_dump(),
        )
    except Exception as e:
        logger.error(
            "Failed to update user profile",
            extra={"user_id": current_user.id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
