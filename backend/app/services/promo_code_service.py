from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.promo_code import PromoCodeCRUD
from app.models.promo_code import PromoCode


class PromoCodeService:
    def __init__(self, session: AsyncSession):
        self.promo_code_crud = PromoCodeCRUD(session)

    async def validate_promo_code(self, code: str) -> PromoCode:
        """
        Проверяет промокод и возвращает его, если он валиден.
        В противном случае выбрасывает HTTPException.
        """
        promo_code = await self.promo_code_crud.get_by_code(code)

        if not promo_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Промокод не найден"
            )

        if not promo_code.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Промокод неактивен"
            )

        if promo_code.uses_left <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Промокод уже использован",
            )

        if promo_code.expires_at and promo_code.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Срок действия промокода истек",
            )

        return promo_code
