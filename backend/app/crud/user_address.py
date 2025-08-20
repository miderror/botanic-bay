from uuid import UUID

from sqlalchemy import Sequence, and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserAddressNotFoundError, UserAddressUpdateError
from app.core.logger import logger
from app.models import User, UserAddress
from app.schemas.order import SUserAddress


class UserAddressCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    # MARK: Create
    async def create(
        self,
        user: User,
        user_address: SUserAddress,
    ) -> UserAddress:
        user_address = UserAddress(
            user=user,
            **user_address.model_dump(),
        )

        try:
            self.session.add(user_address)
            await self.session.commit()
            await self.session.refresh(user_address)
        except IntegrityError:
            await self.session.rollback()
            raise Exception("Вы уже добавляли такой адрес")

        logger.info(
            "Saved new user's address",
            extra={
                "id": str(user_address.id),
                "user_id": str(user_address.user_id),
                "address": str(user_address.address),
            },
        )
        return user_address

    # MARK: Read
    async def get_all(
        self,
        user: User,
    ) -> Sequence[UserAddress] | None:
        query = select(UserAddress).where(
            UserAddress.user_id == user.id,
        )
        result = await self.session.scalars(query)
        return result.all()

    async def get_or_none(
        self,
        *,
        user_id: UUID | None = None,
        address_id: UUID | None = None,
        address: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> UserAddress | None:
        if not any([address_id, address, latitude, longitude]):
            return None
        if latitude or longitude and not all([latitude, longitude]):
            return None

        q = select(UserAddress)
        if user_id:
            q = q.where(UserAddress.user_id == user_id)
        if address_id:
            q = q.where(UserAddress.id == address_id)
        if address:
            q = q.where(UserAddress.address == address)
        if latitude and longitude:
            q = q.where(
                and_(
                    UserAddress.latitude == latitude,
                    UserAddress.longitude == longitude,
                )
            )

        result = await self.session.execute(q)
        point = result.scalar_one_or_none()

        return point

    # MARK: Update
    async def update(
        self,
        *,
        address_id: UUID,
        user_address: SUserAddress,
    ) -> UserAddress:
        """Обновляет дополнительные поля существующего адреса пользователя"""
        query = select(UserAddress).where(
            and_(
                UserAddress.id == address_id,
            )
        )
        result = await self.session.execute(query)
        existing_address = result.scalar_one_or_none()

        if not existing_address:
            raise UserAddressNotFoundError("Адрес не найден")

        # Обновляем только дополнительные поля (не основной адрес)
        existing_address.apartment = user_address.apartment
        existing_address.entrance = user_address.entrance
        existing_address.floor = user_address.floor
        existing_address.intercom_code = user_address.intercom_code

        try:
            await self.session.commit()
            await self.session.refresh(existing_address)
        except IntegrityError:
            await self.session.rollback()
            raise UserAddressUpdateError("Ошибка при обновлении адреса")

        logger.info(
            "Updated user address",
            extra={
                "id": str(existing_address.id),
                "user_id": str(existing_address.user_id),
            },
        )
        return existing_address

    # MARK: Delete
    async def delete(
        self,
        user_address_id: UUID,
    ) -> bool:
        query = select(UserAddress).where(UserAddress.id == user_address_id)
        result = await self.session.execute(query)
        user_address = result.scalar_one_or_none()

        if not user_address:
            return False

        await self.session.delete(user_address)
        await self.session.commit()

        logger.info(
            "User address deleted",
            extra={"user_address_id": str(user_address)},
        )
        return True
