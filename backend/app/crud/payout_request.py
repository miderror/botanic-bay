from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import Sequence, and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.enums.referral import ReferralPayoutStatus
from app.models.referral import PayoutRequest
from app.models.user import User


class PayoutRequestCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, amount: float, payment_details: str) -> PayoutRequest:
        """Создать новую заявку на вывод."""
        req = PayoutRequest(
            user_id=user_id,
            amount=amount,
            payment_details=payment_details,
            status=ReferralPayoutStatus.PENDING,
        )
        self.session.add(req)
        await self.session.commit()
        await self.session.refresh(req)
        return req

    async def get_by_id(self, request_id: UUID) -> Optional[PayoutRequest]:
        """Получить заявку по её ID."""
        q = select(PayoutRequest).where(PayoutRequest.id == request_id)
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        request_id: Optional[UUID] = None,
        status: Optional[ReferralPayoutStatus] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[Sequence[PayoutRequest], int]:
        """Возвращает кортеж (items, total) с учётом фильтров."""
        offset = (page - 1) * page_size
        q_base = select(PayoutRequest).options(joinedload(PayoutRequest.user))

        conditions = []
        if request_id:
            conditions.append(PayoutRequest.id == request_id)
        if status:
            conditions.append(PayoutRequest.status == status)
        if from_date:
            conditions.append(PayoutRequest.created_at >= from_date)
        if to_date:
            conditions.append(PayoutRequest.created_at <= to_date)

        if conditions:
            q_base = q_base.where(and_(*conditions))

        total_q = select(func.count(PayoutRequest.id))
        if conditions:
            total_q = total_q.where(and_(*conditions))
        total_res = await self.session.execute(total_q)
        total = total_res.scalar_one()

        q_page = (
            q_base.order_by(PayoutRequest.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        res = await self.session.execute(q_page)
        items = res.unique().scalars().all()

        return items, total