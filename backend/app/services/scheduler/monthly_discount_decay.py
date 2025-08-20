import pytz
from apscheduler.triggers.cron import CronTrigger

from app.api.deps import get_discount_service
from app.core.db import get_session
from app.services.scheduler import scheduler


@scheduler.scheduled_job(
    CronTrigger(
        day=1,
        hour=0,
        minute=0,
        timezone=pytz.timezone("Europe/Moscow"),
    )
)
async def monthly_discount_decay_task():
    async with get_session() as session:
        service = await get_discount_service(session=session)
        await service.monthly_discount_decay()
