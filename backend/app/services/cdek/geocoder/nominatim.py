import asyncio
from typing import Optional

from geopy.adapters import AioHTTPAdapter
from geopy.geocoders import Nominatim
from geopy.location import Location
from geopy.point import Point

from app.core.logger import logger
from app.services.cdek.geocoder.base import GeocoderService
from app.services.cdek.geocoder.cache import add_region_to_cache, get_cached_region
from app.services.cdek.geocoder.schemas import ParsedLocation


class NominatimGeocoderService(GeocoderService["Nominatim"]):
    def __init__(self):
        self.zoom_levels = {
            "state": 5,
            "settlement": 13,
            "building": 18,
        }

    async def reverse(
        self,
        point: Point,
        exactly_one: bool = True,
        language: str = "ru",
        zoom: int = 13,
        addressdetails: bool = True,
    ) -> Optional[Location]:
        async with Nominatim(
            user_agent="cdek-geocoder",
            adapter_factory=AioHTTPAdapter,
        ) as geolocator:
            try:
                return await geolocator.reverse(
                    point,
                    exactly_one=True,
                    language=language,
                    zoom=zoom,
                    addressdetails=addressdetails,
                )
            except Exception as e:
                logger.error("Failed using geocoder: %s", e)
        return None

    async def get_state(self, point: Point) -> Optional[ParsedLocation]:
        if cached := await get_cached_region(point.latitude, point.longitude):
            return cached

        zoom_level = self.zoom_levels["state"]
        location = await self.reverse(point, zoom=zoom_level)

        if not location:
            return None

        print(location.raw)
        geo_object = location.raw
        address: dict = geo_object.get("address") or {}

        parsed = ParsedLocation(
            country=address.get("country"),
            country_code=address.get("country_code"),
            region=address.get("state"),
            longitude=point.longitude,
            latitude=point.latitude,
            bbox=geo_object.get("boundingbox"),
        )
        await add_region_to_cache(geo_object.get("osm_id"), parsed)
        return parsed

    async def get_building(self, point: Point) -> Optional[ParsedLocation]:
        zoom_level = self.zoom_levels["building"]
        location = await self.reverse(point, zoom=zoom_level)

        if not location:
            return None

        print(location.raw)
        geo_object = location.raw
        address: dict = geo_object.get("address") or {}

        city_types = ["city", "town", "borough", "village", "suburb"]
        city = None
        for city_type in city_types:
            if city_type in address:
                city = address[city_type]
                break

        if not city:
            return None

        return ParsedLocation(
            country=address.get("country"),
            country_code=address.get("country_code"),
            region=address.get("state"),
            city=city,
            address=geo_object.get("display_name"),
            longitude=point.longitude,
            latitude=point.latitude,
        )


async def main():
    geocoder = NominatimGeocoderService()
    point = Point(longitude=52.341611, latitude=55.698931)

    location = await geocoder.get_building(point)
    print("\nLocation: ", location)


if __name__ == "__main__":
    asyncio.run(main())
