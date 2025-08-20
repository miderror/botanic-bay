import functools
from enum import Enum
from typing import Any, Awaitable, Callable, Optional, TypeVar

from pydantic import TypeAdapter
from shapely.geometry import Point, box

from app.core.logger import logger
from app.core.redis import async_redis
from app.services.cdek.geocoder.schemas import ParsedLocation
from app.utils.cache import RedisKeyBuilder

TTL_REGIONS = 86400  # 24 часа


class GeocoderCacheKey(str, Enum):
    REGIONS = "regions"
    REGIONS_GEO = "regions_geo"


class GeocoderRedisKeyBuilder(RedisKeyBuilder):
    def __init__(self):
        super().__init__(service="geocoder")

    def regions(self, region_id: str) -> str:
        return self.build(GeocoderCacheKey.REGIONS + ":" + region_id)

    def regions_geo(self, params: dict = None, *, use_hash: bool = False) -> str:
        return self.build(GeocoderCacheKey.REGIONS_GEO, params, use_hash=use_hash)


async def add_region_to_cache(
    region_id: str,
    location_data: ParsedLocation,
    ttl: int = 86400,
):
    min_lat, max_lat, min_lon, max_lon = location_data.bbox
    # Вычисляем центр bounding box
    center_lon = (min_lon + max_lon) / 2
    center_lat = (min_lat + max_lat) / 2

    # Добавляем в GEO индекс
    await async_redis.geoadd(
        redis_key_builder.regions_geo(),
        [center_lon, center_lat, region_id],
    )
    await async_redis.set(
        redis_key_builder.regions(str(region_id)),
        location_data.model_dump_json(
            exclude_none=True,
            exclude_unset=True,
        ),
        ex=ttl,
    )


async def get_region_details(region_id: str) -> Optional[ParsedLocation]:
    cache_key = redis_key_builder.regions(str(region_id))
    data = await async_redis.get(cache_key)
    if data:
        return TypeAdapter(ParsedLocation).validate_json(data)
    return None


def is_point_in_bbox(point: Point, bbox: tuple) -> bool:
    min_lat, max_lat, min_lon, max_lon = bbox
    region_box = box(min_lon, min_lat, max_lon, max_lat)
    return region_box.contains(point)


async def get_cached_region(lat: float, lon: float) -> Optional[ParsedLocation]:
    point = Point(lon, lat)
    radius_m = 150_000

    candidate_ids = await async_redis.geosearch(
        redis_key_builder.regions_geo(),
        longitude=lon,
        latitude=lat,
        radius=radius_m,
        unit="m",
    )

    print(candidate_ids)

    for region_id in candidate_ids:
        region_data = await get_region_details(region_id)
        print(region_data)
        if region_data and region_data.bbox:
            bbox = tuple(region_data.bbox)
            if is_point_in_bbox(point, bbox):
                logger.info(f"Location from user input found in geo cache: ")
                return region_data
    return None


redis_key_builder = GeocoderRedisKeyBuilder()
