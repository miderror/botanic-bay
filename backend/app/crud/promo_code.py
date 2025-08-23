from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promo_code import PromoCode
from app.schemas.promo_code import SPromoCodeCreate, SPromoCodeUpdate


class PromoCodeCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_code(self, code: str) -> Optional[PromoCode]:
        query = select(PromoCode).where(PromoCode.code == code)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, promo_code_data: SPromoCodeCreate) -> PromoCode:
        promo_code = PromoCode(**promo_code_data.model_dump())
        self.session.add(promo_code)
        await self.session.commit()
        await self.session.refresh(promo_code)
        return promo_code

    async def decrement_uses(self, promo_code_id: UUID) -> Optional[PromoCode]:
        promo_code = await self.session.get(PromoCode, promo_code_id)
        if promo_code and promo_code.uses_left > 0:
            promo_code.uses_left -= 1
            await self.session.commit()
            await self.session.refresh(promo_code)
            return promo_code
        return None