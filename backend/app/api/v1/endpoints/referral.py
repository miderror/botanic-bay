from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.params import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_bot_manager, get_current_user, get_referral_service
from app.core.db import get_session
from app.core.logger import logger
from app.crud.referral import ReferralCRUD
from app.crud.referral_bonus import ReferralBonusCRUD
from app.models.user import User
from app.schemas.referral import (
    SReferral,
    SReferralListPaginated,
    SReferralPayoutRequest,
    SReferralPayoutRequestPaginated,
)
from app.services.referral.referral_service import ReferralService

router = APIRouter()


@router.get("/me", response_model=SReferral)
async def get_referral_details(
    current_user: User = Depends(get_current_user),
    referral_service: ReferralService = Depends(get_referral_service),
):
    try:
        return await referral_service.get_referral_details(user_id=current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch referral details",
            extra={"user_id": str(current_user.id), "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch referral details",
        )


@router.get("/{referral_id}", response_model=SReferral)
async def get_referral_details_by_id(
    referral_id: Annotated[UUID, Path(..., description="ID реферала")],
    current_user: User = Depends(get_current_user),
    referral_service: ReferralService = Depends(get_referral_service),
):
    try:
        return await referral_service.get_referral_details(referral_id=referral_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch referral details",
            extra={"referral_id": str(referral_id), "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch referral details",
        )


@router.get("/me/children", response_model=SReferralListPaginated)
async def get_my_referral_children(
    page: int = Query(1, description="Номер страницы (пагинация)"),
    page_size: int = Query(50, description="Количество элементов на странице"),
    current_user: User = Depends(get_current_user),
    referral_service: ReferralService = Depends(get_referral_service),
):
    try:
        return await referral_service.get_referrer_children(
            user_id=current_user.id,
            page=page,
            page_size=page_size,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch my referral children (paginated)",
            extra={"user_id": str(current_user.id), "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch my referral children (paginated)",
        )


@router.get("/{referral_id}/children", response_model=SReferralListPaginated)
async def get_referral_children(
    referral_id: Annotated[UUID, Path(..., description="ID реферала")],
    page: int = Query(1, description="Номер страницы (пагинация)"),
    page_size: int = Query(50, description="Количество элементов на странице"),
    current_user: User = Depends(get_current_user),
    referral_service: ReferralService = Depends(get_referral_service),
):
    try:
        return await referral_service.get_referrer_children(
            referral_id=referral_id,
            page=page,
            page_size=page_size,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch referral children (paginated)",
            extra={"referral_id": str(referral_id), "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch referral children (paginated)",
        )


@router.post("/me/children/search", response_model=SReferralListPaginated)
async def search_referral_children_by_name(
    name: str = Query(..., description="Имя реферала (подстрока)"),
    page: int = Query(1, description="Номер страницы (пагинация)"),
    page_size: int = Query(50, description="Количество элементов на странице"),
    current_user: User = Depends(get_current_user),
    referral_service: ReferralService = Depends(get_referral_service),
):
    try:
        return await referral_service.search_referrals_by_name(
            current_user.id,
            name=name,
            page=page,
            page_size=page_size,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to search referral children (paginated)",
            extra={"user_id": str(current_user.id), "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search referral children (paginated)",
        )


@router.post("/me/sign_conditions", response_model=SReferral)
async def sign_conditions(
    current_user: User = Depends(get_current_user),
    referral_service: ReferralService = Depends(get_referral_service),
):
    try:
        return await referral_service.sign_conditions(current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to sign referral conditions",
            extra={"user_id": str(current_user.id), "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sign referral conditions",
        )


@router.post("/me/sign_user_terms", response_model=SReferral)
async def sign_user_terms(
    current_user: User = Depends(get_current_user),
    referral_service: ReferralService = Depends(get_referral_service),
):
    try:
        return await referral_service.sign_user_terms(current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to sign referral user terms",
            extra={"user_id": str(current_user.id), "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sign referral user terms",
        )


@router.get("/me/children/top", response_model=SReferralListPaginated)
async def get_top_referral_children(
    current_user: User = Depends(get_current_user),
    referral_service: ReferralService = Depends(get_referral_service),
):
    try:
        return await referral_service.get_top_referrer_children(current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch top referral children",
            extra={"user_id": str(current_user.id), "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch top referral children",
        )


@router.post("/payout-request", response_model=SReferralPayoutRequest)
async def create_payout_request(
    current_user: User = Depends(get_current_user),
    data: SReferralPayoutRequest = Body(...),
    referral_service: ReferralService = Depends(get_referral_service),
):
    try:
        return await referral_service.create_payout_request(
            current_user.id,
            data,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create payout request",
            extra={"user_id": str(current_user.id), "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payout request",
        )
