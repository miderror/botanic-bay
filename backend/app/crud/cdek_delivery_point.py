from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models import CDEKDeliveryPoint
from app.schemas.cdek.response import SDeliveryPoint


class CDEKDeliveryPointCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, delivery_point: SDeliveryPoint) -> CDEKDeliveryPoint:
        point = CDEKDeliveryPoint(
            id=delivery_point.uuid,
            code=delivery_point.code,
            type=delivery_point.type,
            address=delivery_point.location.address_full,
        )

        self.session.add(point)
        await self.session.commit()
        await self.session.refresh(point)

        logger.info(
            "Saved new CDEK Delivery Point in DB",
            extra={
                "id": str(point.id),
                "code": str(point.code),
                "type": str(point.type),
                "address": str(point.address),
            },
        )
        return point

    async def get_or_create(
        self,
        delivery_point: SDeliveryPoint,
    ) -> CDEKDeliveryPoint:
        query = select(CDEKDeliveryPoint).where(
            CDEKDeliveryPoint.id == delivery_point.uuid
        )
        result = await self.session.execute(query)
        point = result.scalar_one_or_none()

        if not point:
            point = await self.create(delivery_point)

        return point

    async def get_or_none(
        self,
        *,
        delivery_point_id: Optional[UUID] = None,
        code: Optional[str] = None,
    ) -> Optional[CDEKDeliveryPoint]:
        if not code and not delivery_point_id:
            return None

        q = select(CDEKDeliveryPoint)
        if delivery_point_id:
            q = q.where(CDEKDeliveryPoint.id == delivery_point_id)
        if code:
            q = q.where(CDEKDeliveryPoint.code == code)

        result = await self.session.execute(q)
        point = result.scalar_one_or_none()

        return point
