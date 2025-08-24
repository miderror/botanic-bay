from http.client import HTTPException
from types import SimpleNamespace
from uuid import UUID

from fastapi import status
from geopy.point import Point
from pydantic import TypeAdapter

from app.core.logger import logger
from app.core.settings import settings
from app.crud.user_address import UserAddressCRUD
from app.crud.user_delivery_point import UserDeliveryPointCRUD
from app.models import CartItem, Order, User, UserAddress
from app.schemas.cdek.base import (
    CalculatorLocation,
    CalculatorPackage,
    Contact,
    Phone,
    RequestLocation,
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
    ) -> TariffCode:
        if not user_address_id and not user_delivery_point_id:
            raise HTTPException(status_code=400, detail="Delivery address or point must be provided")

        to_location_data = {}
        expected_delivery_mode: DeliveryMode

        if user_delivery_point_id:
            user_delivery_point = await self.user_delivery_point_crud.get_or_none(
                point_id=user_delivery_point_id,
            )
            if not user_delivery_point or not user_delivery_point.cdek_delivery_point:
                raise HTTPException(status_code=404, detail="Delivery point not found")
            
            to_location_data = {"address": user_delivery_point.cdek_delivery_point.address}
            expected_delivery_mode = DeliveryMode.WAREHOUSE_TO_WAREHOUSE
        
        elif user_address_id:
            user_address = await self.user_address_crud.get_or_none(
                address_id=user_address_id,
            )
            if not user_address:
                raise HTTPException(status_code=404, detail="User address not found")
            
            to_location_data = {"address": user_address.address}
            expected_delivery_mode = DeliveryMode.WAREHOUSE_TO_DOOR
        else:
            raise HTTPException(status_code=400, detail="No delivery destination provided")

        total_weight = 0
        max_length, max_width, max_height = 0, 0, 0
        for item in items:
            product = item.product
            total_weight += (product.weight or 100) * item.quantity
            max_length = max(max_length, product.length or 100)
            max_width = max(max_width, product.width or 100)
            max_height = max(max_height, product.height or 100)

        if total_weight == 0:
            total_weight = 100

        package = CalculatorPackage(
            weight=total_weight, length=max_length, width=max_width, height=max_height
        )
        
        from_location = CalculatorLocation(address="Россия, Москва, Домодедово (Растуново)")
        to_location = CalculatorLocation(**to_location_data)

        logger.info(
            "Calculating CDEK tariff",
            extra={
                "from": from_location.address,
                "to": to_location.model_dump(),
                "package": package.model_dump(),
            },
        )

        result = await self.cdek_api.calculate_tariff_list(
            TariffListParams(
                from_location=from_location,
                to_location=to_location,
                packages=[package],
            )
        )
        
        logger.debug("CDEK tariff calculation response", extra={"tariffs": result.model_dump()})

        if result.tariff_codes:
            suitable_tariffs = sorted(
                [t for t in result.tariff_codes if t.delivery_mode == expected_delivery_mode],
                key=lambda x: x.delivery_sum,
            )
            if suitable_tariffs:
                cheapest = suitable_tariffs[0]
                logger.info("Cheapest CDEK tariff found with matching mode", extra=cheapest.model_dump())
                return cheapest
            
            all_tariffs_sorted = sorted(result.tariff_codes, key=lambda x: x.delivery_sum)
            if all_tariffs_sorted:
                cheapest_any_mode = all_tariffs_sorted[0]
                logger.warning(
                    "No tariff with expected mode found, returning cheapest available", 
                    extra={
                        "expected_mode": expected_delivery_mode.name,
                        "found_tariff": cheapest_any_mode.model_dump()
                    }
                )
                return cheapest_any_mode

        logger.error(
            "No suitable CDEK tariffs found for the given destination", 
            extra={
                "to_location": to_location_data,
                "cdek_response": result.model_dump()
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось рассчитать стоимость доставки для указанного адреса."
        )

    async def create_cdek_order(self, order: Order, user: User) -> dict | None:
        """Создает заказ в системе СДЭК и возвращает данные, включая трек-номер."""
        logger.info("Creating CDEK order", extra={"order_id": str(order.id)})

        to_location_data = {}
        shipment_point_code = None
        if order.delivery_method == DeliveryMethod.PICKUP and order.delivery_point:
            shipment_point_code = order.delivery_point
        elif (
            order.delivery_method == DeliveryMethod.COURIER
            and order.delivery_to_location
        ):
            to_location_data = {"address": order.delivery_to_location.get("address")}
        else:
            logger.error(
                "Order has no valid delivery info", extra={"order_id": str(order.id)}
            )
            return None

        packages = []
        for i, item in enumerate(order.items):
            product = item.product
            package_item = Item(
                name=product.name[:100],
                ware_key=product.sku or str(product.id),
                cost=float(item.price),
                weight=product.weight or 100,
                amount=item.quantity,
                payment={"value": 0},
            )
            packages.append(
                Package(
                    number=f"{order.id}-{i + 1}",
                    weight=package_item.weight * item.quantity,
                    items=[package_item],
                    length=product.length or 10,
                    width=product.width or 10,
                    height=product.height or 10,
                )
            )

        order_data = OrderCreateForm(
            number=str(order.id),
            tariff_code=order.delivery_tariff_code,
            comment=order.delivery_comment or f"Заказ #{order.id}",
            shipment_point=shipment_point_code,
            recipient=Contact(
                name=user.full_name or "Получатель",
                phones=[Phone(number=user.profile.phone_number or "+79000000000")],
            ),
            from_location=RequestLocation(
                address="Россия, Москва, Домодедово (Растуново)"
            ),
            to_location=RequestLocation(**to_location_data)
            if to_location_data
            else None,
            packages=packages,
        )

        try:
            response = await self.cdek_api.create_order(order_data)

            cdek_order_entity = response.entity
            if cdek_order_entity and cdek_order_entity.uuid:
                logger.info(
                    "CDEK order created successfully",
                    extra={
                        "cdek_uuid": str(cdek_order_entity.uuid),
                        "order_id": str(order.id),
                    },
                )
                return {
                    "cdek_uuid": str(cdek_order_entity.uuid),
                    "track_number": cdek_order_entity.cdek_number,
                }
            else:
                logger.error(
                    "Failed to create CDEK order",
                    extra={
                        "response": response.model_dump(),
                        "order_id": str(order.id),
                    },
                )
                return None
        except Exception as e:
            logger.error(
                "Exception during CDEK order creation",
                extra={"error": str(e), "order_id": str(order.id)},
                exc_info=True,
            )
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
