from typing import Optional
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.crud.user_profile import UserProfileCRUD
from app.models.user import UserProfile
from app.schemas.user import SUserProfile


class ProfileService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.crud = UserProfileCRUD(session)

    async def get_profile(self, user_id: UUID) -> SUserProfile:
        """
        Возвращает профиль пользователя, создавая его, если ещё нет.
        """
        return SUserProfile.model_validate(await self.crud.get_or_create(user_id))

    async def update_profile(
        self,
        user_id: UUID,
        *,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
    ) -> SUserProfile:
        logger.info(
            "Updating user profile",
            extra={
                "user_id": str(user_id),
                "full_name": full_name,
                "phone_number": phone_number,
                "email": email,
            },
        )
        return SUserProfile.model_validate(
            await self.crud.update(
                user_id,
                full_name=full_name,
                phone_number=phone_number,
                email=email,
            )
        )

    async def update_name(self, user_id: UUID, full_name: str) -> SUserProfile:
        return await self.update_profile(user_id, full_name=full_name)

    async def update_phone(self, user_id: UUID, phone_number: str) -> SUserProfile:
        return await self.update_profile(user_id, phone_number=phone_number)

    async def update_email(self, user_id: UUID, email: str) -> SUserProfile:
        return await self.update_profile(user_id, email=email)
