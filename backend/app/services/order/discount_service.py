from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.settings import settings
from app.crud.order import OrderCRUD
from app.crud.user_discount import UserDiscountCRUD
from app.models.order_status import OrderStatus
from app.schemas.user import SUserDiscountProgress, UserDiscountLevel


class DiscountService:
    # Определяем порядок уровней от низшего к высшему
    LEVEL_ORDER = [
        UserDiscountLevel.NONE,
        UserDiscountLevel.BRONZE,
        UserDiscountLevel.SILVER,
        UserDiscountLevel.GOLD,
    ]

    # Словари порогов и процентов для каждого уровня
    LEVEL_THRESHOLDS = {
        UserDiscountLevel.BRONZE: Decimal(settings.BRONZE_DISCOUNT_THRESHOLD),
        UserDiscountLevel.SILVER: Decimal(settings.SILVER_DISCOUNT_THRESHOLD),
        UserDiscountLevel.GOLD: Decimal(settings.GOLD_DISCOUNT_THRESHOLD),
    }
    LEVEL_PERCENTS = {
        UserDiscountLevel.BRONZE: Decimal(settings.BRONZE_DISCOUNT_PERCENT),
        UserDiscountLevel.SILVER: Decimal(settings.SILVER_DISCOUNT_PERCENT),
        UserDiscountLevel.GOLD: Decimal(settings.GOLD_DISCOUNT_PERCENT),
    }

    def __init__(
        self,
        session: AsyncSession,
        discount_crud: UserDiscountCRUD,
        order_crud: OrderCRUD,
    ):
        self.session = session
        self.discount_crud = discount_crud
        self.order_crud = order_crud

    async def on_order_paid(self, user_id: UUID, order_id: UUID):
        """
        Вызывается, когда заказ переходит в статус PAID.
        Обновляет last_purchase_date и повышает уровень, если нужно.
        """
        order = await self.order_crud.get_order(order_id)
        if order.status != OrderStatus.PAID:
            return

        today = date.today()
        month_start = today.replace(day=1)

        # 1) Сумма доставленных заказов за текущий месяц
        monthly_total: Decimal = await self.order_crud.get_monthly_total(
            user_id, month_start
        )

        # 2) Определяем новый уровень по сумме
        new_level = UserDiscountLevel.NONE
        for level in reversed(self.LEVEL_ORDER[1:]):  # пробегаем GOLD→SILVER→BRONZE
            threshold = self.LEVEL_THRESHOLDS[level]
            if monthly_total >= threshold:
                new_level = level
                break

        # 3) Загружаем или создаём запись скидки
        record = await self.discount_crud.get_or_create(user_id)

        # 4) Обновляем дату последней покупки, если это первая покупка в месяце
        last_purchase = today if monthly_total > 0 else record.last_purchase_date

        # 5) Не занижаем достигнутый уровень, если сумма упала
        current_index = self.LEVEL_ORDER.index(record.current_level)
        new_index = self.LEVEL_ORDER.index(new_level)
        final_index = max(current_index, new_index)
        final_level = self.LEVEL_ORDER[final_index]

        # 6) Сохраняем
        await self.discount_crud.update(
            user_id,
            level=final_level,
            last_purchase=last_purchase,
        )

    async def get_progress_to_next_level(self, user_id: UUID) -> SUserDiscountProgress:
        """
        Возвращает информацию:
          - current_total: сколько уже потрачено в этом месяце
          - required_total: порог для следующего уровня (0 если уже на максимуме)
          - amount_left: сколько до порога осталось
          - next_level: следующий UserDiscountLevel
          - next_percent: процент скидки для следующего уровня
        """
        logger.info("Getting user discount progress", extra={"user_id": user_id})

        monthly_total: Decimal = await self.order_crud.get_monthly_total(user_id)
        record = await self.discount_crud.get_or_create(user_id)
        current_index = self.LEVEL_ORDER.index(record.current_level)

        # Если уже на максимальном уровне
        if current_index == len(self.LEVEL_ORDER) - 1:
            percent = float(self.LEVEL_PERCENTS.get(record.current_level, 0))
            return SUserDiscountProgress(
                current_percent=percent,
                current_total=float(monthly_total),
                current_level=record.current_level,
                required_total=0,
                amount_left=0,
                next_level=record.current_level,
                next_percent=percent,
            )

        # Ищем следующий уровень
        next_level = self.LEVEL_ORDER[current_index + 1]
        threshold = self.LEVEL_THRESHOLDS[next_level]
        amount_left = max(Decimal("0.0"), threshold - monthly_total)
        next_percent = self.LEVEL_PERCENTS[next_level]
        current_percent = float(self.LEVEL_PERCENTS.get(record.current_level, 0))

        return SUserDiscountProgress(
            current_percent=current_percent,
            current_total=float(monthly_total),
            current_level=record.current_level,
            required_total=float(threshold),
            amount_left=float(amount_left),
            next_level=next_level,
            next_percent=float(next_percent),
        )

    async def monthly_discount_decay(self):
        """
        Понижает уровень скидки на один шаг тем пользователям,
        которые не совершали покупок в прошлом месяце.
        """
        # высчитываем границы прошлого месяца
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month_end = start_of_month - timedelta(seconds=1)
        prev_month_start = prev_month_end.replace(day=1)

        # получаем всех с текущей скидкой выше NONE
        users = await self.discount_crud.get_users_with_discount()

        for record in users:
            had_order = await self.order_crud.has_orders_in_range(
                user_id=record.user_id,
                start_date=prev_month_start,
                end_date=prev_month_end,
            )
            if not had_order:
                # понижаем уровень
                curr_index = self.LEVEL_ORDER.index(record.current_level)
                new_index = max(0, curr_index - 1)
                new_level = self.LEVEL_ORDER[new_index]
                await self.discount_crud.update_discount_level(
                    record.user_id, new_level
                )

    async def get_current_discount_percent(self, user_id: UUID) -> float:
        record = await self.discount_crud.get_or_create(user_id)
        percent = self.LEVEL_PERCENTS.get(record.current_level, Decimal("0.0"))
        return float(percent)

    async def get_discount_multiplier(self, user_id: UUID) -> Decimal:
        record = await self.discount_crud.get_or_create(user_id)
        percent = self.LEVEL_PERCENTS.get(record.current_level, Decimal(0))
        multiplier = (Decimal(100) - percent) / Decimal(100)
        return multiplier.quantize(Decimal("0.0001"))
