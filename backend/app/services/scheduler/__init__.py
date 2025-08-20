from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(
    job_defaults={
        "misfire_grace_time": 15,  # разрешить задержку до 15 сек
        # "max_instances": 3,  # разрешить 3 параллельных выполнения
    }
)

from . import (
    monthly_discount_decay,
)
