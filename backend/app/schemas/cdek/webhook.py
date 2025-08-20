from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.cdek.base import Entity
from app.schemas.cdek.enums import (
    ModificationNewValueType,
    ModificationType,
    OrderType,
    WebhookType,
)


class WebhookResponse(BaseModel):
    type: WebhookType
    date_time: datetime
    uuid: UUID
    attributes: list[Any]


class OrderStatusAttributes(BaseModel):
    is_return: bool
    cdek_number: str
    number: UUID
    status_reason_code: Optional[str] = None
    status_date_time: datetime
    city_name: Optional[str] = None
    city_code: Optional[str] = None
    code: str
    is_reverse: bool
    is_client_return: bool
    related_entities: Optional[list[Entity]] = None
    type: OrderType
    uuid: UUID


class OrderModifiedAttributes(BaseModel):
    modification_type: ModificationType
    new_value: Any
    type: ModificationNewValueType
    value: datetime | float | int | str


class WebhookOrderStatus(WebhookResponse):
    attributes: list[OrderStatusAttributes] = []


class WebhookOrderModifiedStatus(WebhookResponse):
    attributes: list[OrderModifiedAttributes] = []
