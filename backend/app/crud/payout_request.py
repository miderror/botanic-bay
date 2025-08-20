from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import Sequence, and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.enums.referral import ReferralPayoutStatus
from app.models.referral import Referral, ReferralPayoutRequest


class ReferralPayoutRequestCRUD:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        referrer_id: UUID,
        bank_code: str,
        account_number: str,
        amount: float,
    ) -> ReferralPayoutRequest:
        """
        Создать новую заявку на вывод.
        """
        req = ReferralPayoutRequest(
            referrer_id=referrer_id,
            bank_code=bank_code,
            account_number=account_number,
            amount=amount,
            status=ReferralPayoutStatus.PENDING,
        )
        self.session.add(req)
        await self.session.commit()
        await self.session.refresh(req)
        return req

    async def get_by_id(self, request_id: UUID) -> Optional[ReferralPayoutRequest]:
        """
        Получить заявку по её ID.
        """
        q = select(ReferralPayoutRequest).where(ReferralPayoutRequest.id == request_id)
        res = await self.session.execute(q)
        return res.scalar_one_or_none()

    async def list_by_referrer(
        self, referrer_id: UUID, page: int = 1, page_size: int = 50
    ) -> Tuple[Sequence[ReferralPayoutRequest], int]:
        """
        Вернуть страницу заявок данного реферера и общее количество.
        """
        offset = (page - 1) * page_size

        # общее число
        total_q = select(func.count(ReferralPayoutRequest.id)).where(
            ReferralPayoutRequest.referrer_id == referrer_id
        )
        total_res = await self.session.execute(total_q)
        total = total_res.scalar_one()

        # сами заявки
        q = (
            select(ReferralPayoutRequest)
            .where(ReferralPayoutRequest.referrer_id == referrer_id)
            .order_by(ReferralPayoutRequest.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        res = await self.session.execute(q)
        items = res.scalars().all()

        return items, total

    async def update_status(
        self,
        request_id: UUID,
        new_status: ReferralPayoutStatus,
    ) -> Optional[ReferralPayoutRequest]:
        """
        Обновить статус заявки.
        """
        q = (
            update(ReferralPayoutRequest)
            .where(ReferralPayoutRequest.id == request_id)
            .values(status=new_status)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.execute(q)
        await self.session.commit()
        return await self.get_by_id(request_id)

    async def delete(self, request_id: UUID) -> None:
        """
        Удалить заявку.
        """
        q = delete(ReferralPayoutRequest).where(ReferralPayoutRequest.id == request_id)
        await self.session.execute(q)
        await self.session.commit()

    async def list_by_status(
        self, status: ReferralPayoutStatus, page: int = 1, page_size: int = 50
    ) -> Tuple[Sequence[ReferralPayoutRequest], int]:
        """
        Вернуть страницу заявок с указанным статусом и общее количество таких заявок.
        """
        offset = (page - 1) * page_size

        # 1) общее число заявок с данным статусом
        total_q = select(func.count(ReferralPayoutRequest.id)).where(
            ReferralPayoutRequest.status == status
        )
        total_res = await self.session.execute(total_q)
        total = total_res.scalar_one()

        # 2) сами заявки
        q = (
            select(ReferralPayoutRequest)
            .where(ReferralPayoutRequest.status == status)
            .order_by(ReferralPayoutRequest.id.desc())
            .limit(page_size)
            .offset(offset)
        )
        res = await self.session.execute(q)
        items = res.scalars().all()

        return items, total

    async def list_with_filters(
        self,
        *,
        request_id: Optional[UUID] = None,
        status: Optional[ReferralPayoutStatus] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[Sequence[ReferralPayoutRequest], int]:
        """
        Возвращает кортеж (items, total) с учётом фильтров:
        - request_id  — фильтр по самому ID заявки
        - status      — статус PENDING/APPROVED/REJECTED
        - from_date   — created_at >= from_date
        - to_date     — created_at <= to_date
        Пагинация — page, page_size.
        """
        offset = (page - 1) * page_size

        # базовый запрос
        q_base = select(ReferralPayoutRequest).options(
            joinedload(ReferralPayoutRequest.referrer).joinedload(Referral.user)
        )

        # собираем условия
        conditions = []
        if request_id:
            conditions.append(ReferralPayoutRequest.id == request_id)
        if status:
            conditions.append(ReferralPayoutRequest.status == status)
        if from_date:
            conditions.append(ReferralPayoutRequest.created_at >= from_date)
        if to_date:
            conditions.append(ReferralPayoutRequest.created_at <= to_date)

        if conditions:
            q_base = q_base.where(and_(*conditions))

        # общее число
        total_q = select(func.count(ReferralPayoutRequest.id))
        if conditions:
            total_q = total_q.where(and_(*conditions))
        total_res = await self.session.execute(total_q)
        total = total_res.scalar_one()

        # страницы
        q_page = (
            q_base.order_by(ReferralPayoutRequest.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        res = await self.session.execute(q_page)
        items = res.unique().scalars().all()

        return items, total
