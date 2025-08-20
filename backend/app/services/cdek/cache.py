import functools
from typing import Any, Awaitable, Callable, TypeVar

from pydantic import TypeAdapter

from app.core.logger import logger
from app.core.redis import async_redis
from app.schemas.cdek.enums import CDEKCacheKey
from app.utils.cache import RedisKeyBuilder

T = TypeVar("T")


TTL_REGIONS_AND_CITIES = 86400  # 24 часа
TTL_PICKUP_POINTS = 10800  # 3 часа


class CDEKRedisKeyBuilder(RedisKeyBuilder):
    def __init__(self):
        super().__init__(service="cdek")

    def regions(self, params: dict = None, *, use_hash: bool = False) -> str:
        return self.build(CDEKCacheKey.REGIONS, params, use_hash=use_hash)

    def cities(self, params: dict = None, *, use_hash: bool = False) -> str:
        return self.build(CDEKCacheKey.CITIES, params, use_hash=use_hash)

    def delivery_points(self, params: dict = None, *, use_hash: bool = False) -> str:
        return self.build(CDEKCacheKey.DELIVERY_POINTS, params, use_hash=use_hash)


def cache_endpoint(
    cache_key_builder: Callable[..., str],
    ttl: int,
    type_adapter: TypeAdapter[T],
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    Декоратор для кэширования результатов асинхронных эндпоинтов.

    :param cache_key_builder: функция, принимающая аргументы эндпоинта и возвращающая ключ для Redis.
    :param ttl: время жизни кэша в секундах.
    :param type_adapter: TypeAdapter для сериализации/десериализации результата.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache_key = cache_key_builder(*args, **kwargs)
            cached = await async_redis.get(cache_key)
            if cached:
                logger.info(f"Returning data from cache: {cache_key}")
                return type_adapter.validate_json(cached)
            result = await func(*args, **kwargs)
            await async_redis.set(cache_key, type_adapter.dump_json(result), ex=ttl)
            return result

        return wrapper

    return decorator


redis_key_builder = CDEKRedisKeyBuilder()
