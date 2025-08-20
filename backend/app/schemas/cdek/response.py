from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.cdek.base import (
    Entity,
    EntityRequest,
    ErrorDto,
    OfficeLocation,
    OfficeWorkTime,
    OrderEntity,
    Phone,
    TariffCode,
    WarningDto,
    WebhookEntity,
)
from app.schemas.cdek.enums import OfficeType


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    scope: str
    jti: str


class RegionResponse(BaseModel):
    region: str
    region_code: int | None = None
    country: str
    country_code: str


class CityResponse(BaseModel):
    code: int
    city_uuid: UUID
    city: str
    fias_guid: UUID | None = None
    country_code: str
    country: str
    region: str
    region_code: int | None = None
    sub_region: str | None = None
    longitude: float | None = None
    latitude: float | None = None
    time_zone: str | None = None
    payment_limit: float = -1


class DeliveryPointResponse(BaseModel):
    code: str
    uuid: str
    work_time: str
    phones: list[Phone] = []
    type: OfficeType
    owner_code: str
    take_only: bool
    is_handout: bool
    is_reception: bool
    is_dressing_room: bool
    have_cashless: bool
    have_cash: bool
    have_fast_payment_system: bool
    allowed_cod: bool
    work_time_list: list[OfficeWorkTime] = []
    location: OfficeLocation


class TariffListResponse(BaseModel):
    tariff_codes: list[TariffCode] = []
    errors: list[ErrorDto] = []
    warnings: list[WarningDto] = []


class OrderCreationResponse(BaseModel):
    entity: Entity
    requests: list[EntityRequest]


class OrderInfoResponse(BaseModel):
    entity: OrderEntity
    requests: list[EntityRequest]


class WebhookCreationResponse(BaseModel):
    entity: WebhookEntity
    requests: list[EntityRequest]


class WebhookDeletionResponse(BaseModel):
    entity: WebhookEntity
    requests: list[EntityRequest]


class SDeliveryPoint(BaseModel):
    uuid: UUID
    code: str
    location: OfficeLocation
    work_time: str
    type: OfficeType

    model_config = ConfigDict(
        extra="ignore",
    )


class SAddress(BaseModel):
    address: str
    address_full: str | None = None
    latitude: float
    longitude: float

    model_config = ConfigDict(
        extra="ignore",
    )


class SAddressSearchResult(BaseModel):
    """Результат поиска адреса для доставки"""

    id: str
    title: str
    subtitle: str
    full_address: str
    country: str | None = None
    city: str | None = None
    street: str | None = None
    house: str | None = None
    latitude: float
    longitude: float
    distance_km: float | None = None

    model_config = ConfigDict(
        extra="ignore",
    )


class SDeliveryPointSearchResult(BaseModel):
    """Результат поиска ПВЗ"""

    id: str
    title: str
    subtitle: str
    address: str
    latitude: float
    longitude: float
    distance_km: float | None = None
    work_time: str
    office_type: str

    model_config = ConfigDict(
        extra="ignore",
    )
