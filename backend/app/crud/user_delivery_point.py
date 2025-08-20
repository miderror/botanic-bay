from typing import List, Optional
from uuid import UUID

from sqlalchemy import Sequence, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.logger import logger
from app.models import CDEKDeliveryPoint, User, UserDeliveryPoint


class UserDeliveryPointCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user: User,
        cdek_delivery_point: CDEKDeliveryPoint,
    ) -> UserDeliveryPoint:
        user_delivery_point = UserDeliveryPoint(
            user=user,
            cdek_delivery_point=cdek_delivery_point,
        )

        try:
            self.session.add(user_delivery_point)
            await self.session.commit()
            await self.session.refresh(user_delivery_point)
        except IntegrityError:
            await self.session.rollback()
            raise Exception("Вы уже добавляли такой пункт выдачи")

        logger.info(
            "Saved new user's delivery point",
            extra={
                "id": str(user_delivery_point.id),
                "user_id": str(user_delivery_point.user_id),
                "cdek_delivery_point_id": str(
                    user_delivery_point.cdek_delivery_point_id
                ),
            },
        )
        return user_delivery_point

    async def get_all(self, user: User) -> Optional[Sequence[UserDeliveryPoint]]:
        query = (
            select(UserDeliveryPoint)
            .options(joinedload(UserDeliveryPoint.cdek_delivery_point))
            .where(UserDeliveryPoint.user_id == user.id)
        )
        result = await self.session.scalars(query)
        return result.all()

    async def delete(self, user_delivery_point_id: UUID) -> bool:
        query = select(UserDeliveryPoint).where(
            UserDeliveryPoint.id == user_delivery_point_id
        )
        result = await self.session.execute(query)
        point = result.scalar_one_or_none()

        if not point:
            return False

        await self.session.delete(point)
        await self.session.commit()

        logger.info(
            "User delivery point deleted",
            extra={"user_delivery_point_id": str(user_delivery_point_id)},
        )
        return True

    async def get_or_none(
        self,
        *,
        point_id: Optional[UUID] = None,
        cdek_delivery_point_id: Optional[UUID] = None,
    ) -> Optional[UserDeliveryPoint]:
        if not any([point_id, cdek_delivery_point_id]):
            return None

        q = select(UserDeliveryPoint).options(
            joinedload(UserDeliveryPoint.cdek_delivery_point)
        )
        if point_id:
            q = q.where(UserDeliveryPoint.id == point_id)
        if cdek_delivery_point_id:
            q = q.where(
                UserDeliveryPoint.cdek_delivery_point_id == cdek_delivery_point_id
            )

        result = await self.session.execute(q)
        point = result.scalar_one_or_none()

        return point
