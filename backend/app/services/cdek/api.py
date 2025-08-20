import asyncio
import json
import os
import time
from typing import Any, Optional, Type
from uuid import UUID

import httpx
from pydantic import BaseModel, TypeAdapter

from app.core.logger import logger
from app.core.redis import async_redis
from app.schemas.cdek.base import ErrorDto, WebhookEntity
from app.schemas.cdek.request import (
    CitiesParams,
    DeliveryPointsParams,
    OAuthTokenForm,
    OrderCreateForm,
    OrderInfoParams,
    RegionsParams,
    TariffListParams,
    WebhookCreateForm,
)
from app.schemas.cdek.response import (
    CityResponse,
    DeliveryPointResponse,
    OAuthTokenResponse,
    OrderCreationResponse,
    OrderInfoResponse,
    RegionResponse,
    TariffListResponse,
    WebhookCreationResponse,
    WebhookDeletionResponse,
)
from app.services.cdek.cache import (
    TTL_PICKUP_POINTS,
    TTL_REGIONS_AND_CITIES,
    CDEKRedisKeyBuilder,
    cache_endpoint,
    redis_key_builder,
)
from app.services.cdek.client import CDEKAsyncClient


class CDEKApi:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        client: CDEKAsyncClient,
        credentials_file: str = "credentials.json",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.credentials_file = credentials_file
        self.client: CDEKAsyncClient = client
        # При инициализации пытаемся загрузить сохранённый токен, только если токен отсутствует или устарел
        current_time = time.monotonic()
        if not self.client.access_token or current_time >= self.client.token_expires_at:
            self.load_credentials()

    def load_credentials(self) -> None:
        if os.path.exists(self.credentials_file):
            try:
                with open(self.credentials_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    token = data.get("access_token", "")
                    expires_at = data.get("token_expires_at", 0.0)
                    current_time = time.monotonic()
                    if token and current_time < expires_at:
                        self.client.token = token
                        self.client.token_expires_at = expires_at
                        logger.info("Token loaded from file.")
                    else:
                        logger.info("Token in file is missing or expired.")
            except Exception as e:
                logger.error(f"Error loading credentials: {e}")

    def save_credentials(self) -> None:
        data = {
            "access_token": self.client.access_token,
            "token_expires_at": self.client.token_expires_at,
        }
        try:
            with open(self.credentials_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
                logger.info("Token saved to file.")
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")

    async def get_token(self) -> None:
        """Request a new token and save it in the global client."""
        try:
            response = await self.client.post(
                "/v2/oauth/token",
                data=OAuthTokenForm(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                ).model_dump(),
            )
            response.raise_for_status()
            token_data = OAuthTokenResponse.model_validate(response.json())
            self.client.access_token = token_data.access_token

            loop = asyncio.get_running_loop()
            self.client.token_expires_at = loop.time() + token_data.expires_in

            self.save_credentials()
            logger.info("New token obtained successfully.")
        except Exception as e:
            logger.error(f"Error obtaining token: {e}")
            raise

    async def ensure_token(self) -> None:
        """Ensure that a valid token is available in the global client.
        Load from file only if token is missing or expired."""
        current_time = asyncio.get_event_loop().time()
        if not self.client.access_token or current_time >= self.client.token_expires_at:
            # Attempt to load from file first
            self.load_credentials()
            if (
                not self.client.access_token
                or current_time >= self.client.token_expires_at
            ):
                await self.get_token()

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        request_model: Optional[BaseModel] = None,
        response_model: Optional[Type[BaseModel] | Type[list[BaseModel]]] = None,
        **kwargs: Any,
    ) -> Any:
        await self.ensure_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.client.access_token}"
        kwargs["headers"] = headers

        if request_model is not None:
            kwargs["json"] = request_model.model_dump(exclude_none=True)

        try:
            response = await self.client.request(method, endpoint, **kwargs)
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            raise

        response_json = response.json()

        if response.status_code >= 400:
            try:
                type_adapter = TypeAdapter(ErrorDto)
                if isinstance(response_json, dict) and "errors" in response_json:
                    type_adapter = TypeAdapter(list[ErrorDto])
                    error_content = response_json["errors"]
                else:
                    error_content = response_json
                errors = type_adapter.validate_json(json.dumps(error_content))
                logger.error(f"API Error(s): {errors}")
            except Exception as e:
                logger.error(f"Error processing error response: {e}")
                response.raise_for_status()
            return

        if response_model is not None:
            return self._parse_response(response_json, response_model)
        return response_json

    @staticmethod
    def _parse_response(
        response_json: Any, response_model: Type[BaseModel] | Type[list[BaseModel]]
    ) -> Any:
        try:
            json_str = json.dumps(response_json)
            type_adapter = TypeAdapter(response_model)
            return type_adapter.validate_json(json_str)
        except Exception as e:
            logger.error(f"Error parsing response into model {response_model}: {e}")
            raise

    async def add_webhook(self, data: WebhookCreateForm) -> WebhookCreationResponse:
        return await self.request(
            "POST",
            "/v2/webhooks",
            request_model=data,
            response_model=WebhookCreationResponse,
        )

    async def delete_webhook(self, webhook_uuid: UUID) -> WebhookDeletionResponse:
        return await self.request(
            "DELETE",
            f"/v2/webhooks/{webhook_uuid}",
            response_model=WebhookDeletionResponse,
        )

    async def get_webhooks(self) -> list[WebhookEntity]:
        return await self.request(
            "GET",
            "/v2/webhooks",
            response_model=list[WebhookEntity],
        )

    @cache_endpoint(
        cache_key_builder=lambda self, data: redis_key_builder.regions(
            data.model_dump(), use_hash=True
        ),
        ttl=TTL_REGIONS_AND_CITIES,
        type_adapter=TypeAdapter(list[RegionResponse]),
    )
    async def get_regions(self, data: RegionsParams) -> list[RegionResponse]:
        return await self.request(
            "GET",
            "/v2/location/regions",
            params=data.model_dump(),
            response_model=list[RegionResponse],
        )

    @cache_endpoint(
        cache_key_builder=lambda self, data: redis_key_builder.cities(
            data.model_dump(), use_hash=True
        ),
        ttl=TTL_REGIONS_AND_CITIES,
        type_adapter=TypeAdapter(list[CityResponse]),
    )
    async def get_cities(self, data: CitiesParams) -> list[CityResponse]:
        return await self.request(
            "GET",
            "/v2/location/cities",
            params=data.model_dump(),
            response_model=list[CityResponse],
        )

    async def calculate_tariff_list(self, data: TariffListParams) -> TariffListResponse:
        return await self.request(
            "POST",
            "/v2/calculator/tarifflist",
            request_model=data,
            response_model=TariffListResponse,
        )

    @cache_endpoint(
        cache_key_builder=lambda self, data: redis_key_builder.delivery_points(
            data.model_dump(), use_hash=True
        ),
        ttl=TTL_PICKUP_POINTS,
        type_adapter=TypeAdapter(list[DeliveryPointResponse]),
    )
    async def get_delivery_points(
        self, data: DeliveryPointsParams
    ) -> list[DeliveryPointResponse]:
        return await self.request(
            "GET",
            "/v2/deliverypoints",
            params=data.model_dump(),
            response_model=list[DeliveryPointResponse],
        )

    async def create_order(self, data: OrderCreateForm) -> OrderCreationResponse:
        return await self.request(
            "POST",
            "/v2/orders",
            request_model=data,
            response_model=OrderCreationResponse,
        )

    async def get_order_info(self, data: OrderInfoParams) -> OrderInfoResponse:
        return await self.request(
            "GET",
            "/v2/orders",
            params=data.model_dump(),
            response_model=OrderInfoResponse,
        )

    async def close(self) -> None:
        await self.client.aclose()
