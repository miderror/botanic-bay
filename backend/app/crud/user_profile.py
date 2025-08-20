from datetime import date
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserDiscount, UserProfile
from app.schemas.user import UserDiscountLevel


class UserProfileCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: UUID) -> UserProfile:
        q = select(UserProfile).where(UserProfile.user_id == user_id)
        res = await self.session.execute(q)
        profile = res.unique().scalar_one_or_none()
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.session.add(profile)
            await self.session.commit()
            await self.session.refresh(profile)
        return profile

    async def update(
        self,
        user_id: UUID,
        *,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
    ) -> UserProfile:
        vals = {}
        if full_name is not None:
            vals["full_name"] = full_name
        if phone_number is not None:
            vals["phone_number"] = phone_number
        if email is not None:
            vals["email"] = email

        if vals:
            await self.session.execute(
                update(UserProfile).where(UserProfile.user_id == user_id).values(**vals)
            )
            await self.session.commit()

        return await self.get_or_create(user_id)
