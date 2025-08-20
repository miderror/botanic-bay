from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_cdek_service, get_current_user
from app.core.logger import logger
from app.models.user import User
from app.schemas.cdek.request import (
    AddressSearchParams,
    CenterPoint,
    DeliveryPointSearchParams,
)
from app.schemas.cdek.response import (
    SAddress,
    SAddressSearchResult,
    SDeliveryPoint,
    SDeliveryPointSearchResult,
)
from app.services.cdek.cdek_service import CDEKService

router = APIRouter()


@router.get("/delivery_points", response_model=list[SDeliveryPoint])
async def get_pickup_points(
    center: Annotated[
        CenterPoint,
        Depends(lambda center: CenterPoint.from_query(center)),
    ],
    current_user: User = Depends(get_current_user),
    cdek_service: CDEKService = Depends(get_cdek_service),
):
    try:
        return await cdek_service.get_delivery_points(center)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get pickup points for the location",
            extra={"user_id": str(current_user.id), "center": center},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pickup points from CDEK API",
        )


@router.get("/address", response_model=SAddress)
async def get_address(
    point: Annotated[CenterPoint, Depends(lambda point: CenterPoint.from_query(point))],
    current_user: User = Depends(get_current_user),
    cdek_service: CDEKService = Depends(get_cdek_service),
):
    try:
        return await cdek_service.get_address(point)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get address for the location",
            extra={"user_id": str(current_user.id), "point": point},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch address from Geocoder",
        )


@router.post("/webhooks/order_status")
async def webhook_order_status(
    point: Annotated[CenterPoint, Depends(lambda point: CenterPoint.from_query(point))],
    current_user: User = Depends(get_current_user),
    cdek_service: CDEKService = Depends(get_cdek_service),
):
    try:
        return await cdek_service.get_address(point)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get address for the location",
            extra={"user_id": str(current_user.id), "point": point},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch address from Geocoder",
        )


@router.get("/search/addresses", response_model=list[SAddressSearchResult])
async def search_delivery_addresses(
    query: str = Query(
        ...,
        min_length=3,
        max_length=200,
        description="Поисковый запрос адреса",
    ),
    user_latitude: Optional[float] = Query(
        None,
        ge=-90,
        le=90,
        description="Широта местоположения пользователя",
    ),
    user_longitude: Optional[float] = Query(
        None,
        ge=-180,
        le=180,
        description="Долгота местоположения пользователя",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Максимальное количество результатов",
    ),
    current_user: User = Depends(get_current_user),
    cdek_service: CDEKService = Depends(get_cdek_service),
):
    """Поиск адресов для доставки по текстовому запросу"""
    try:
        params = AddressSearchParams(
            query=query,
            user_latitude=user_latitude,
            user_longitude=user_longitude,
            limit=limit,
        )
        return await cdek_service.search_delivery_addresses(params)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to search delivery addresses",
            extra={"user_id": str(current_user.id), "query": query},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search delivery addresses",
        )


@router.get("/search/delivery-points", response_model=list[SDeliveryPointSearchResult])
async def search_delivery_points_by_address(
    address_query: str = Query(
        ...,
        min_length=3,
        max_length=200,
        description="Адрес для поиска ближайших ПВЗ",
    ),
    user_latitude: Optional[float] = Query(
        None, ge=-90, le=90, description="Широта местоположения пользователя"
    ),
    user_longitude: Optional[float] = Query(
        None, ge=-180, le=180, description="Долгота местоположения пользователя"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=20,
        description="Максимальное количество ПВЗ в результатах",
    ),
    current_user: User = Depends(get_current_user),
    cdek_service: CDEKService = Depends(get_cdek_service),
):
    """Поиск ПВЗ по адресу пользователя с расчетом расстояния от его местоположения"""
    try:
        params = DeliveryPointSearchParams(
            address_query=address_query,
            user_latitude=user_latitude,
            user_longitude=user_longitude,
            limit=limit,
        )
        return await cdek_service.search_delivery_points_by_address(params)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to search delivery points by address",
            extra={"user_id": str(current_user.id), "address_query": address_query},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search delivery points by address",
        )
