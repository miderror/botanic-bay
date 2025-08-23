from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.user import User
from app.schemas.promo_code import SPromoCodeApply, SPromoCodeApplyResponse
from app.services.promo_code_service import PromoCodeService

router = APIRouter()


async def get_promo_code_service(
    session: AsyncSession = Depends(get_session),
) -> PromoCodeService:
    return PromoCodeService(session)


@router.post("/apply", response_model=SPromoCodeApplyResponse)
async def apply_promo_code(
    data: SPromoCodeApply,
    _: User = Depends(get_current_user),
    promo_code_service: PromoCodeService = Depends(get_promo_code_service),
):
    """Проверяет валидность промокода и возвращает информацию о скидке."""
    try:
        promo_code = await promo_code_service.validate_promo_code(data.code)
        return SPromoCodeApplyResponse(
            code=promo_code.code,
            discount_percent=float(promo_code.discount_percent),
            is_valid=True,
            message="Промокод успешно применен",
        )
    except HTTPException as e:
        return SPromoCodeApplyResponse(
            code=data.code,
            discount_percent=0.0,
            is_valid=False,
            message=e.detail,
        )
