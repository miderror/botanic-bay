from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.cdek.enums import (
    ContragentType,
    DeliveryMode,
    PaymentType,
    RequestState,
    RequestType,
    WebhookType,
)


class ErrorDto(BaseModel):
    code: str
    message: str


class WarningDto(BaseModel):
    code: str
    message: str


class Status(BaseModel):
    code: str
    name: str
    date_time: datetime
    reason_code: Optional[str] = None
    city: str
    city_uuid: UUID
    deleted: bool


class Money(BaseModel):
    value: float
    vat_sum: Optional[float] = None
    vat_rate: Optional[int] = None


class PaymentInfo(BaseModel):
    type: PaymentType
    sum: float


class Phone(BaseModel):
    number: str
    additional: Optional[str] = None


class Contact(BaseModel):
    company: Optional[str] = None
    name: str
    email: Optional[str] = None
    phones: list[Phone]


class Location(BaseModel):
    address: str


class CalculatorLocation(Location):
    code: Optional[int] = None
    postal_code: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    contragent_type: Optional[ContragentType] = None


class Service(BaseModel):
    code: str
    parameter: Optional[str] = None


class Item(BaseModel):
    name: str
    ware_key: str
    payment: Money
    cost: float
    weight: int
    amount: int


class Package(BaseModel):
    number: str
    weight: int
    length: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    comment: Optional[str] = None
    items: Optional[list[Item]] = None


class CalculatorPackage(BaseModel):
    weight: int
    length: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class OfficeWorkTime(BaseModel):
    day: int
    periods: list[str] = []  # Default empty list


class OfficeLocation(Location):
    country_code: str
    region_code: int
    region: str
    city_code: int
    city: str
    latitude: float
    longitude: float
    address_full: str


class RequestLocation(Location):
    code: Optional[str] = None
    city_uuid: Optional[UUID] = None
    city: Optional[str] = None
    country_code: Optional[str] = None
    country: Optional[str] = None
    region_code: Optional[int] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TariffCode(BaseModel):
    tariff_code: int
    tariff_name: str
    delivery_mode: DeliveryMode
    delivery_sum: float
    period_min: int
    period_max: int


class DeliveryDetail(BaseModel):
    date: Optional[datetime] = None
    recipient_name: Optional[str] = None
    payment_sum: Optional[float] = None
    delivery_sum: float
    total_sum: float
    payment_info: Optional[PaymentInfo] = None
    delivery_vat_rate: Optional[float] = None
    delivery_vat_sum: Optional[float] = None
    delivery_discount_percent: Optional[float] = None
    delivery_discount_sum: Optional[float] = None


class DeliveryProblem(BaseModel):
    code: str
    create_date: datetime


class FailedCall(BaseModel):
    date_time: datetime
    reason_code: int


class RescheduledCall(BaseModel):
    date_time: datetime
    date_next: datetime
    time_next: datetime
    comment: Optional[str] = None


class Calls(BaseModel):
    failed_calls: Optional[list[FailedCall]] = None
    rescheduled_calls: Optional[list[RescheduledCall]] = None


class Entity(BaseModel):
    uuid: UUID


class OrderEntity(Entity):
    type: int
    additional_order_types: Optional[list[int]] = None
    is_return: bool
    is_reverse: bool
    cdek_number: Optional[str] = None
    number: Optional[str] = None
    accompanying_number: Optional[str] = None
    tariff_code: int
    comment: Optional[str] = None
    shipment_point: Optional[str] = None
    delivery_point: Optional[str] = None
    keep_free_until: Optional[str] = None
    sender: Optional[Contact] = None
    recipient: Contact
    from_location: RequestLocation
    packages: list[Package]
    statuses: list[Status]
    is_client_return: bool
    delivery_mode: str
    planned_delivery_date: datetime
    delivery_detail: Optional[DeliveryDetail] = None
    delivery_problem: Optional[list[DeliveryProblem]] = None
    calls: Optional[list[Calls]] = None


class WebhookEntity(Entity):
    type: WebhookType
    url: str


class EntityRequest(BaseModel):
    request_uuid: Optional[UUID] = None
    type: RequestType
    date_time: datetime
    state: RequestState
    errors: Optional[list[ErrorDto]] = None
    warnings: Optional[list[WarningDto]] = None
