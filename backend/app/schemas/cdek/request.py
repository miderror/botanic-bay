from datetime import datetime
from typing import Optional
from uuid import UUID

from geopy.point import Point
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.cdek.base import (
    CalculatorLocation,
    CalculatorPackage,
    Contact,
    Package,
    RequestLocation,
)
from app.schemas.cdek.enums import OfficeType, WebhookType


class QueryParams(BaseModel):
    model_config = ConfigDict(
        json_encoders={bool: lambda v: int(v)},
        extra="ignore",
    )

    def dict(self, *args, **kwargs):
        return super().dict(*args, **{**kwargs, "exclude_none": True})

    def model_dump(self, *args, **kwargs):
        cleaned_data = super().model_dump(*args, **kwargs)
        return {
            key: value
            for key, value in cleaned_data.items()
            if value not in [None, [], {}]
        }


class OAuthTokenForm(BaseModel):
    grant_type: str = "client_credentials"
    client_id: str
    client_secret: str


class RegionsParams(QueryParams):
    country_codes: Optional[list[str]] = None
    size: Optional[int] = None
    page: Optional[int] = None


class CitiesParams(QueryParams):
    country_codes: Optional[list[str]] = None
    region_code: Optional[int] = None
    fias_guid: Optional[UUID] = None
    postal_code: Optional[str] = None
    code: Optional[str] = None
    city: Optional[str] = None
    payment_limit: Optional[float] = None
    size: Optional[int] = None
    page: Optional[int] = None


class DeliveryPointsParams(QueryParams):
    code: Optional[str] = None
    type: Optional[OfficeType] = None
    postal_code: Optional[str] = None
    city_code: Optional[int] = None
    region_code: Optional[int] = None
    allowed_cod: Optional[bool] = None
    fias_guid: Optional[UUID] = None
    size: Optional[int] = None
    page: Optional[int] = None


class OrderInfoParams(QueryParams):
    cdek_number: Optional[int] = None
    im_number: Optional[str] = None


class TariffListParams(QueryParams):
    date: Optional[datetime] = None
    type: Optional[int] = 1
    additional_order_types: Optional[list[int]] = None
    currency: Optional[int] = None
    lang: Optional[str] = None
    from_location: CalculatorLocation
    to_location: CalculatorLocation
    packages: list[CalculatorPackage]


class OrderCreateForm(BaseModel):
    uuid: Optional[UUID] = None
    type: int = 1
    additional_order_types: Optional[list[int]] = None
    number: str
    accompanying_number: Optional[str] = None
    tariff_code: int
    comment: Optional[str] = None
    recipient: Contact
    from_location: RequestLocation
    to_location: Optional[RequestLocation] = None
    shipment_point: Optional[str] = None
    packages: list[Package]


class WebhookCreateForm(BaseModel):
    type: WebhookType
    url: str


class CenterPoint(Point):
    @classmethod
    def from_query(cls, value: str) -> "CenterPoint":
        try:
            lon_str, lat_str = value.split(",")
            return cls(latitude=lat_str, longitude=lon_str)
        except Exception:
            raise ValueError("Invalid center format. Use 'lon,lat'")


class Bounds(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

    @classmethod
    def from_query(cls, value: str) -> "Bounds":
        try:
            part1, part2 = value.split("~")
            x1, y1 = map(float, part1.split(","))
            x2, y2 = map(float, part2.split(","))
            return cls(x1=x1, y1=y1, x2=x2, y2=y2)
        except Exception:
            raise ValueError("Invalid bounds format. Use 'x1,y1~x2,y2'")


class AddressSearchParams(BaseModel):
    """Параметры поиска адресов для доставки"""

    query: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Поисковый запрос адреса",
    )
    user_latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Широта местоположения пользователя",
    )
    user_longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Долгота местоположения пользователя",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Максимальное количество результатов",
    )


class DeliveryPointSearchParams(BaseModel):
    """Параметры поиска ПВЗ по адресу"""

    address_query: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Адрес для поиска ближайших ПВЗ",
    )
    user_latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="Широта местоположения пользователя",
    )
    user_longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Долгота местоположения пользователя",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Максимальное количество ПВЗ в результатах",
    )
