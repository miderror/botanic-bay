from redis import asyncio as aioredis

from app.core.settings import settings

redis_args = dict(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
)
async_redis = aioredis.Redis(**redis_args)
