from datetime import date
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserDiscount
from app.schemas.user import UserDiscountLevel


class UserDiscountCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: UUID) -> UserDiscount:
        q = select(UserDiscount).where(UserDiscount.user_id == user_id)
        res = await self.session.execute(q)
        disc = res.unique().scalar_one_or_none()
        if not disc:
            disc = UserDiscount(user_id=user_id)
            self.session.add(disc)
            await self.session.commit()
            await self.session.refresh(disc)
        return disc

    async def update(
        self,
        user_id: UUID,
        *,
        level: UserDiscountLevel | None = None,
        last_purchase: date | None = None,
    ) -> UserDiscount:
        vals = {}
        if level is not None:
            vals["current_level"] = level
        if last_purchase is not None:
            vals["last_purchase_date"] = last_purchase

        if vals:
            await self.session.execute(
                update(UserDiscount)
                .where(UserDiscount.user_id == user_id)
                .values(**vals)
            )
            await self.session.commit()

        return await self.get_or_create(user_id)

    async def get_users_with_discount(self) -> Sequence[UserDiscount]:
        q = select(UserDiscount).where(
            UserDiscount.current_level != UserDiscountLevel.NONE
        )
        result = await self.session.execute(q)
        return result.scalars().all()

    async def update_discount_level(
        self,
        user_id: UUID,
        new_level: UserDiscountLevel,
    ) -> None:
        q = (
            update(UserDiscount)
            .where(UserDiscount.user_id == user_id)
            .values(discount_level=new_level)
        )
        await self.session.execute(q)
        await self.session.commit()
