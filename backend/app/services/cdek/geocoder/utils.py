import re
from typing import Optional

from app.schemas.cdek.response import RegionResponse


def normalize_region_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r"\bреспублика\b", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def find_region_by_name(
    geocoder_region: str,
    regions: list[RegionResponse],
) -> Optional[RegionResponse]:
    normalized_geocoder = normalize_region_name(geocoder_region)
    for region in regions:
        normalized_api_region = normalize_region_name(region.region)
        if (
            normalized_geocoder in normalized_api_region
            or normalized_api_region in normalized_geocoder
        ):
            return region
    return None
