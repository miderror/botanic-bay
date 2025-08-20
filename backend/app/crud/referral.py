from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import Row, RowMapping, and_, delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload, selectinload

from app.core.logger import logger
from app.models import Order, User
from app.models.order_status import OrderStatus
from app.models.referral import Referral, ReferralBonus
from app.schemas.referral import ReferralChild, ReferralChildBonus


class ReferralCRUD:
    """CRUD для модели Referral."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: UUID, referrer_id: Optional[UUID] = None
    ) -> Referral:
        referral = Referral(
            user_id=user_id,
            referrer_id=referrer_id,
        )
        self.session.add(referral)
        await self.session.commit()
        await self.session.refresh(referral)

        logger.info(
            "Created new referral",
            extra={"user_id": str(user_id), "referrer_id": str(referrer_id)},
        )
        return referral

    async def get(
        self, *, referral_id: UUID | None = None, user_id: UUID | None = None
    ) -> Referral | None:
        if not referral_id and not user_id:
            raise ValueError("Either referral_id or user_id must be provided")

        q = select(Referral).options(
            joinedload(Referral.user),
            joinedload(Referral.referrer),
        )
        if referral_id:
            q = q.where(Referral.id == referral_id)
        if user_id:
            q = q.where(Referral.user_id == user_id)

        res = await self.session.execute(q)
        return res.unique().scalar_one_or_none()

    async def get_or_create(
        self,
        *,
        user_id: Optional[UUID] = None,
        referral_id: Optional[UUID] = None,
        referrer_id: Optional[UUID] = None,
    ) -> Referral:
        if not (referral := await self.get(user_id=user_id, referral_id=referral_id)):
            return await self.create(user_id, referrer_id)
        return referral

    async def get_children_paginated(
        self, referrer_id: UUID, page: int = 1, page_size: int = 50
    ) -> Sequence[Referral]:
        offset = (page - 1) * page_size
        q = (
            select(Referral)
            .where(Referral.referrer_id == referrer_id)
            .order_by(Referral.id)
            .limit(page_size)
            .offset(offset)
            .options(joinedload(Referral.user))
        )
        res = await self.session.execute(q)
        return res.scalars().all()

    async def search_children_by_name(
        self, referrer_id: UUID, name_substr: str, page: int = 1, page_size: int = 50
    ) -> Tuple[list[ReferralChild], int]:
        """
        Ищет direct-рефералов по имени и возвращает:
          - list[ReferralChild] на текущей странице
          - общее число совпадений (total) для pagination
        """
        # 1) считаем общее число совпадений
        total_q = (
            select(func.count(Referral.id))
            .join(User, User.id == Referral.user_id)
            .where(
                Referral.referrer_id == referrer_id,
                User.full_name.ilike(f"%{name_substr}%"),
            )
        )
        total_res = await self.session.execute(total_q)
        total = total_res.scalar_one()

        # 2) получаем страницу с подсчетом детей у каждого
        offset = (page - 1) * page_size
        child = aliased(Referral)

        page_q = (
            select(Referral, func.count(child.id).label("child_count"))
            .join(User, User.id == Referral.user_id)
            .outerjoin(child, child.referrer_id == Referral.id)
            .where(
                Referral.referrer_id == referrer_id,
                User.full_name.ilike(f"%{name_substr}%"),
            )
            .group_by(Referral.id)
            .order_by(Referral.id)
            .limit(page_size)
            .offset(offset)
            .options(joinedload(Referral.user))
        )
        page_res = await self.session.execute(page_q)

        items: list[ReferralChild] = []
        for r, cnt in page_res.all():
            items.append(
                ReferralChild(
                    referral=r,
                    referral_count=int(cnt),
                )
            )

        return items, total

    async def update_balance(self, user_id: UUID, new_balance: Decimal) -> None:
        await self.session.execute(
            update(Referral)
            .where(Referral.user_id == user_id)
            .values(balance=new_balance)
        )
        await self.session.commit()

    async def increment_balance(self, user_id: UUID, amount: Decimal | float) -> None:
        await self.session.execute(
            update(Referral)
            .where(Referral.user_id == user_id)
            .values(balance=Referral.balance + amount)
        )
        await self.session.commit()

    async def update_signed_flags(
        self,
        user_id: UUID,
        *,
        signed_conditions: Optional[bool] = None,
        signed_user_terms: Optional[bool] = None,
    ) -> None:
        vals = {}
        if signed_conditions is not None:
            vals["signed_conditions"] = signed_conditions
        if signed_user_terms is not None:
            vals["signed_user_terms"] = signed_user_terms

        if not vals:
            return

        await self.session.execute(
            update(Referral).where(Referral.user_id == user_id).values(**vals)
        )
        await self.session.commit()

    async def delete(self, user_id: UUID) -> None:
        await self.session.execute(delete(Referral).where(Referral.user_id == user_id))
        await self.session.commit()

    async def get_children_amount(self, referrer_id: UUID) -> int:
        q = select(func.count(Referral.id)).where(Referral.referrer_id == referrer_id)
        res = await self.session.execute(q)
        return res.scalar_one()

    async def get_children_with_counts(
        self, referrer_id: UUID, page: int = 1, page_size: int = 50
    ) -> Tuple[list[ReferralChild], int]:
        """
        Возвращает (список ReferralChild на странице, общее число direct-рефералов).

        ReferralChild содержит:
            - referral     : сам объект Referral
            - referral_count: сколько детей у этого referral
        """
        # 1) Считаем общее число direct-рефералов
        total_q = select(func.count(Referral.id)).where(
            Referral.referrer_id == referrer_id
        )
        total_res = await self.session.execute(total_q)
        total = total_res.scalar_one()

        # 2) Подтягиваем саму страницу с подсчётом детей
        offset = (page - 1) * page_size
        child = aliased(Referral)

        page_q = (
            select(Referral, func.count(child.id).label("child_count"))
            .outerjoin(child, child.referrer_id == Referral.id)
            .where(Referral.referrer_id == referrer_id)
            .group_by(Referral.id)
            .order_by(Referral.id)
            .limit(page_size)
            .offset(offset)
            .options(selectinload(Referral.user))
        )
        page_res = await self.session.execute(page_q)

        items: list[ReferralChild] = []
        for r, cnt in page_res.all():
            items.append(
                ReferralChild(
                    referral=r,
                    referral_count=int(cnt),
                )
            )

        return items, total

    async def get_top_children_by_bonus(
        self,
        referrer_id: UUID,
        limit: int = 10,
    ) -> List[ReferralChildBonus]:
        """
        Возвращает топ-N прямых рефералов данного referrer_id,
        с двумя метриками:
          - lifetime_bonus: сумма всех бонусов из referral_bonuses
          - current_month_orders_count: количество доставленных заказов за текущий месяц
        """
        now = datetime.now(tz=timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        BonusAlias = aliased(ReferralBonus)
        OrderAlias = aliased(Order)

        q = (
            select(
                Referral,
                # Сумма всех бонусов (lifetime)
                func.coalesce(func.sum(BonusAlias.bonus_amount), 0).label(
                    "lifetime_bonus"
                ),
                # Счётчик доставленных заказов в этом месяце
                func.count(OrderAlias.id).label("current_month_orders_count"),
            )
            # джойн по истории бонусов
            .outerjoin(BonusAlias, BonusAlias.referral_id == Referral.id)
            # джойн по доставленным заказам в месяце
            .outerjoin(
                OrderAlias,
                (OrderAlias.user_id == Referral.user_id)
                & (OrderAlias.status == OrderStatus.DELIVERED)
                & (OrderAlias.created_at >= start_of_month),
            )
            .where(Referral.referrer_id == referrer_id)
            .group_by(Referral.id)
            .order_by(desc("lifetime_bonus"))
            .limit(limit)
            .options(selectinload(Referral.user))
        )

        res = await self.session.execute(q)

        out: List[ReferralChildBonus] = []
        for referral, lifetime_bonus, month_count in res.all():
            out.append(
                ReferralChildBonus(
                    referral=referral,
                    # lifetime_bonus=float(lifetime_bonus),
                    current_month_orders=int(month_count),
                )
            )
        return out
