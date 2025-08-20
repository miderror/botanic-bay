from types import SimpleNamespace
from uuid import UUID

from geopy.point import Point
from pydantic import TypeAdapter

from app.core.logger import logger
from app.core.settings import settings
from app.crud.user_address import UserAddressCRUD
from app.crud.user_delivery_point import UserDeliveryPointCRUD
from app.models import CartItem, User, UserAddress
from app.schemas.cdek.base import (
    CalculatorLocation,
    CalculatorPackage,
    Contact,
    Phone,
    TariffCode,
)
from app.schemas.cdek.enums import DeliveryMode, RequestState, RequestType, WebhookType
from app.schemas.cdek.request import (
    AddressSearchParams,
    CenterPoint,
    CitiesParams,
    DeliveryPointSearchParams,
    DeliveryPointsParams,
    OrderCreateForm,
    RegionsParams,
    TariffListParams,
    WebhookCreateForm,
)
from app.schemas.cdek.response import (
    RegionResponse,
    SAddress,
    SAddressSearchResult,
    SDeliveryPoint,
    SDeliveryPointSearchResult,
)
from app.services.cdek.api import CDEKApi
from app.services.cdek.geocoder.nominatim import NominatimGeocoderService
from app.services.cdek.geocoder.schemas import ParsedLocation
from app.services.cdek.geocoder.utils import find_region_by_name
from app.services.cdek.geocoder.yandex import YandexGeocoderService


class CDEKService:
    def __init__(
        self,
        cdek_api: CDEKApi,
        geocoder_service: NominatimGeocoderService,
        yandex_geocoder_service: YandexGeocoderService,
        user_address_crud: UserAddressCRUD,
        user_delivery_point_crud: UserDeliveryPointCRUD,
    ):
        self.cdek_api = cdek_api
        self.geocoder_service = geocoder_service
        self.yandex_geocoder_service = yandex_geocoder_service
        self.user_address_crud = user_address_crud
        self.user_delivery_point_crud = user_delivery_point_crud

    async def _setup_webhooks(self):
        webhooks_mappingg = {
            WebhookType.ORDER_STATUS: "order_status",
            WebhookType.ORDER_MODIFIED: "order_modified",
            WebhookType.OFFICE_AVAILABILITY: "office_availability",
            WebhookType.DELIV_PROBLEM: "deliv_problem",
            WebhookType.DELIV_AGREEMENT: "deliv_agreement",
        }
        base_url = settings.CDEK_WEBHOOK_URL

        for webhook in await self.cdek_api.get_webhooks():
            url = "/".join([base_url, webhooks_mappingg.get(webhook.type)])
            if webhook.type in webhooks_mappingg.keys() and webhook.url != url:
                await self.cdek_api.delete_webhook(webhook.uuid)
                await self.cdek_api.add_webhook(
                    WebhookCreateForm(type=webhook.type, url=url),
                )
                del webhooks_mappingg[webhook.type]

        forms = [
            WebhookCreateForm(
                type=_type,
                url="/".join([base_url, webhooks_mappingg[_type]]),
            )
            for _type in webhooks_mappingg
        ]

        for form in forms:
            await self.cdek_api.add_webhook(form)

    async def _get_delivery_points_by_city(
        self, location: ParsedLocation, regions: list[RegionResponse]
    ):
        city_to_get = CitiesParams(
            country_codes=[location.country_code],
            city=location.city,
        )

        if found_region := find_region_by_name(location.region, regions):
            city_to_get.region_code = found_region.region_code

        city = (await self.cdek_api.get_cities(city_to_get))[0]
        delivery_points = await self.cdek_api.get_delivery_points(
            DeliveryPointsParams(
                city_code=city.code,
                region_code=city.region_code,
            )
        )
        return delivery_points

    async def _get_delivery_points_by_state(
        self, location: ParsedLocation, regions: list[RegionResponse]
    ):
        if found_region := find_region_by_name(location.region, regions):
            region_code = found_region.region_code

            delivery_points = await self.cdek_api.get_delivery_points(
                DeliveryPointsParams(
                    region_code=region_code,
                )
            )
            return delivery_points
        return []

    async def get_delivery_points(self, center: CenterPoint) -> list[SDeliveryPoint]:
        location = await self.geocoder_service.get_state(center)
        if not location:
            return []

        regions = await self.cdek_api.get_regions(
            RegionsParams(country_codes=[location.country_code]),
        )
        delivery_points = await self._get_delivery_points_by_state(location, regions)

        return TypeAdapter(
            list[SDeliveryPoint],
        ).validate_python([dp.dict() for dp in delivery_points])

    async def get_address(self, point: CenterPoint) -> SAddress | None:
        location = await self.geocoder_service.get_building(point)
        if not location:
            return None

        return SAddress.model_validate(location.dict())

    async def calculate_cheapest_tariff(
        self,
        items: list[CartItem],
        user_address_id: UUID | None = None,
        user_delivery_point_id: UUID | None = None,
    ) -> TariffCode | None:
        if not user_address_id and not user_delivery_point_id:
            return None

        delivery_mode = DeliveryMode.DOOR_TO_WAREHOUSE
        additional_order_types = [7]
        address: str = ""

        user_address = await self.user_address_crud.get_or_none(
            address_id=user_address_id,
        )
        user_delivery_point = await self.user_delivery_point_crud.get_or_none(
            point_id=user_delivery_point_id,
        )

        if user_address:
            delivery_mode = DeliveryMode.DOOR_TO_DOOR
            address = user_address.address
        if user_delivery_point:
            address = user_delivery_point.cdek_delivery_point.address

        if not address:
            return None

        result = await self.cdek_api.calculate_tariff_list(
            TariffListParams(
                additional_order_types=additional_order_types,
                # TODO call warehouse API to get an actual address
                from_location=CalculatorLocation(
                    address="Москва, Домодедово (Растуново)"
                ),
                to_location=CalculatorLocation(address=address),
                # TODO call warehouse API to get items and calc their weight individually
                packages=[
                    CalculatorPackage(
                        width=None,
                        height=None,
                        length=None,
                        weight=500,  # граммы
                    )
                    for _ in items
                ],
            )
        )

        if result.tariff_codes:
            tariff_codes: list[TariffCode] = sorted(
                filter(
                    lambda code: code.delivery_mode == delivery_mode,
                    result.tariff_codes,
                ),
                key=lambda x: (x.delivery_sum, x.period_min),
            )
            return tariff_codes[0]

        return None

    @staticmethod
    def _get_recipient(user: User):
        return Contact(
            name=user.full_name,
            phones=[
                Phone(number="+79000000000"),
            ],
        )

    @staticmethod
    def _get_order_comment(user_address: UserAddress) -> str:
        comment_data = {
            "квартира": user_address.apartment,
            "подъезд": user_address.entrance,
            "этаж": user_address.floor,
            "код домофона": user_address.intercom_code,
        }
        return ", ".join(
            [": ".join([key, value]) for key, value in comment_data.items() if value]
        ).capitalize()

    async def create_order(self, user: User, db_order_id: UUID) -> bool:
        order_data = OrderCreateForm(
            number=db_order_id,
            tariff_code=59,
            comment=self._get_order_comment(),
            recipient=self._get_recipient(user),
        )

        order = await self.cdek_api.create_order(order_data)
        request_states = [RequestState.ACCEPTED, RequestState.SUCCESSFUL]

        for request in order.requests:
            if request.type == RequestType.CREATE and request.state in request_states:
                await self._setup_webhooks()

                logger.info(
                    "Order successfully placed at CDEK",
                    exc_info={
                        "im_number": order_data.number,
                    },
                )
                return True

        return False

    async def search_delivery_addresses(
        self,
        params: AddressSearchParams,
    ) -> list[SAddressSearchResult]:
        """
        Поиск адресов для доставки по текстовому запросу.

        Args:
            params: Параметры поиска адресов

        Returns:
            Список найденных адресов с координатами
        """
        user_location = None
        if params.user_latitude is not None and params.user_longitude is not None:
            user_location = Point(params.user_latitude, params.user_longitude)

        # Используем YandexGeocoderService для поиска адресов
        parsed_locations = await self.yandex_geocoder_service.search_addresses(
            query=params.query,
            user_location=user_location,
            limit=params.limit,
        )

        # Преобразуем результаты в схему ответа
        results = []
        for i, location in enumerate(parsed_locations):
            # Формируем адрес в нужном формате: "Улица, дом, город, страна"
            address_parts = []

            # Добавляем улицу и дом (если есть в поле address)
            if location.address and location.address.strip():
                address_parts.append(location.address.strip())

            # Добавляем город
            if location.city and location.city.strip():
                address_parts.append(location.city.strip())

            # Добавляем страну
            if location.country and location.country.strip():
                address_parts.append(location.country.strip())

            formatted_address = ", ".join(address_parts)

            result = SAddressSearchResult(
                id=f"addr_{i}_{location.latitude}_{location.longitude}",
                title=formatted_address or "Адрес",
                subtitle=location.region or "Регион не указан",
                full_address=formatted_address or "Неизвестный адрес",
                country=location.country,
                city=location.city,
                street=location.street,
                house=location.house,
                latitude=location.latitude,
                longitude=location.longitude,
                distance_km=getattr(location, "distance_km", None),
            )
            results.append(result)

        return results

    async def search_delivery_points_by_address(
        self,
        params: DeliveryPointSearchParams,
    ) -> list[SDeliveryPointSearchResult]:
        """
        Поиск ПВЗ по адресу пользователя с расчетом расстояния от его местоположения.

        Args:
            params: Параметры поиска ПВЗ по адресу

        Returns:
            Отсортированный список ПВЗ с расчетом расстояний
        """
        user_location = None
        if params.user_latitude is not None and params.user_longitude is not None:
            user_location = Point(params.user_latitude, params.user_longitude)

        # Сначала нужно получить все доступные ПВЗ в регионе
        # Для этого геокодируем адрес, чтобы понять регион
        found_addresses = await self.yandex_geocoder_service.search_addresses(
            query=params.address_query, limit=1
        )

        if not found_addresses:
            logger.warning(
                f"Could not geocode address for delivery points search: {params.address_query}"
            )
            return []

        target_location = Point(
            found_addresses[0].latitude, found_addresses[0].longitude
        )

        # Получаем ПВЗ в регионе через существующий метод
        delivery_points = await self.get_delivery_points(
            center=CenterPoint(target_location.latitude, target_location.longitude)
        )

        # Если нет ПВЗ в регионе, возвращаем пустой список
        if not delivery_points:
            return []

        # Используем YandexGeocoderService для поиска ближайших ПВЗ с учетом расстояний
        # Преобразуем SDeliveryPoint в формат, который ожидает find_nearest_delivery_points_by_address
        delivery_points_for_search = []
        for point in delivery_points:
            # Создаем простой объект с нужными атрибутами
            point_obj = SimpleNamespace(
                location=SimpleNamespace(
                    latitude=point.location.latitude,
                    longitude=point.location.longitude,
                ),
                uuid=point.uuid,
                code=point.code,
                work_time=point.work_time,
                type=point.type,
            )
            delivery_points_for_search.append(point_obj)

        # Находим ближайшие ПВЗ с учетом расстояний
        nearest_points = (
            await self.yandex_geocoder_service.find_nearest_delivery_points_by_address(
                address_query=params.address_query,
                delivery_points=delivery_points_for_search,
                user_location=user_location,
                target_location=target_location,
                limit=params.limit,
            )
        )

        # Преобразуем результаты в схему ответа
        results = []
        for point in nearest_points:
            # Находим исходный SDeliveryPoint по uuid для получения полной информации
            original_point = next(
                (dp for dp in delivery_points if str(dp.uuid) == str(point.uuid)), None
            )

            if original_point:
                result = SDeliveryPointSearchResult(
                    id=str(point.uuid),
                    title=f"ПВЗ {point.code}",
                    subtitle=original_point.location.address or "Адрес не указан",
                    address=original_point.location.address or "Адрес не указан",
                    latitude=point.location.latitude,
                    longitude=point.location.longitude,
                    distance_km=getattr(point, "distance_from_user_km", None),
                    work_time=point.work_time or "Время работы не указано",
                    office_type=(
                        str(point.type.value)
                        if hasattr(point.type, "value")
                        else str(point.type)
                    ),
                )
                results.append(result)

        return results
