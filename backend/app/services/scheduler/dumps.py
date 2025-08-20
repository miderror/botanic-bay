from apscheduler.triggers.interval import IntervalTrigger
from project.db.dumps import create_pg_dump, delete_pg_dumps
from project.scheduler import scheduler


@scheduler.scheduled_job(IntervalTrigger(days=1))
def create_dump_schedule():
    create_pg_dump()


@scheduler.scheduled_job(IntervalTrigger(days=1))
def delete_dump_schedule():
    delete_pg_dumps()
