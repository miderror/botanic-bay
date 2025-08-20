from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.referral import ReferralBonus


class ReferralBonusCRUD:
    """CRUD операции для работы с бонусами по реферальной программе"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        referrer_id: UUID,
        referral_id: UUID,
        bonus_amount: float | Decimal,
        order_id: Optional[UUID],
    ) -> ReferralBonus:
        bonus = ReferralBonus(
            referrer_id=referrer_id,
            referral_id=referral_id,
            order_id=order_id,
            bonus_amount=bonus_amount,
        )
        self.session.add(bonus)
        await self.session.commit()
        await self.session.refresh(bonus)

        logger.info(
            "Referral bonus created",
            extra={
                "referrer_id": str(referrer_id),
                "referral_id": str(referral_id),
                "order_id": str(order_id),
                "bonus_amount": float(bonus_amount),
            },
        )

        return bonus

    async def get_by_referrer(self, referrer_id: UUID) -> Sequence[ReferralBonus]:
        query = select(ReferralBonus).where(ReferralBonus.referrer_id == referrer_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_total_bonus_for_referrer(self, referrer_id: UUID) -> float:
        query = select(func.sum(ReferralBonus.bonus_amount)).where(
            ReferralBonus.referrer_id == referrer_id
        )
        result = await self.session.execute(query)
        total = result.scalar()
        return float(total or 0)

    async def get_total_bonus_for_referral(self, referral_id: UUID) -> float:
        query = select(func.sum(ReferralBonus.bonus_amount)).where(
            ReferralBonus.referral_id == referral_id
        )
        result = await self.session.execute(query)
        total = result.scalar()
        return float(total or 0)

    async def delete_by_order(self, order_id: UUID) -> None:
        await self.session.execute(
            delete(ReferralBonus).where(ReferralBonus.order_id == order_id)
        )
        await self.session.commit()

    async def get_available_balance(
        self, referrer_id: UUID, min_age_days: int = 30
    ) -> Decimal:
        """
        Сумма бонусов по referrer_id, которым больше `min_age_days` и которые не были отменены,
        **минус** сумма всех заявок на вывод (pending + approved) для этого реферера.
        """
        cutoff = datetime.utcnow() - timedelta(days=min_age_days)

        # 1) Сумма всех «созревших» бонусов
        bonuses_q = select(
            func.coalesce(func.sum(ReferralBonus.bonus_amount), 0)
        ).where(
            ReferralBonus.referrer_id == referrer_id,
            ReferralBonus.created_at <= cutoff,
            ReferralBonus.reverted_at.is_(None),
        )
        bonuses_res = await self.session.execute(bonuses_q)
        total_bonuses = bonuses_res.scalar_one()

        # 2) Сумма всех уже запрошенных (pending + approved)
        from app.enums.referral import ReferralPayoutStatus
        from app.models.referral import ReferralPayoutRequest

        payouts_q = select(
            func.coalesce(func.sum(ReferralPayoutRequest.amount), 0)
        ).where(
            ReferralPayoutRequest.referrer_id == referrer_id,
            ReferralPayoutRequest.status == ReferralPayoutStatus.PENDING,
        )
        payouts_res = await self.session.execute(payouts_q)
        total_requested = payouts_res.scalar_one()

        # 3) Доступный остаток
        return total_bonuses - total_requested

    async def revert_bonuses_for_order(self, order_id: UUID) -> int:
        """
        Помечает все бонусы по данному заказу как отменённые.
        Возвращает число отменённых записей.
        """
        stmt = (
            update(ReferralBonus)
            .where(
                ReferralBonus.order_id == order_id, ReferralBonus.reverted_at.is_(None)
            )
            .values(reverted_at=datetime.utcnow())
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return res.rowcount()
