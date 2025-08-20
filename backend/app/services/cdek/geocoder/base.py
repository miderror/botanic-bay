from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar

from geopy import Location, Point

T = TypeVar("T", bound="GeocoderService")


class GeocoderService(ABC, Generic[T]):
    @abstractmethod
    async def reverse(
        self,
        point: Point,
        exactly_one: bool = True,
    ) -> Optional[Location]:
        pass
