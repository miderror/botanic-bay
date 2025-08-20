from geopy import distance
from geopy.adapters import AioHTTPAdapter
from geopy.exc import GeocoderInsufficientPrivileges, GeocoderServiceError
from geopy.geocoders import Yandex
from geopy.location import Location
from geopy.point import Point

from app.core.logger import logger
from app.services.cdek.geocoder.base import GeocoderService
from app.services.cdek.geocoder.schemas import ParsedLocation


class YandexGeocoderService(GeocoderService["YandexGeocoderService"]):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def reverse(
        self,
        point: Point,
        exactly_one: bool = True,
        kind: str = None,
    ) -> Location | None:
        async with Yandex(
            api_key=self.api_key,
            adapter_factory=AioHTTPAdapter,
            timeout=10,
        ) as geolocator:
            try:
                return await geolocator.reverse(
                    point, exactly_one=exactly_one, kind=kind
                )
            except Exception as e:
                logger.error("Failed using geocoder: %s", e)
        return None

    async def search_addresses(
        self,
        query: str,
        user_location: Point | None = None,
        limit: int = 10,
    ) -> list[ParsedLocation]:
        """
        Поиск адресов по текстовому запросу (прямое геокодирование).

        Args:
            query: Текстовый запрос для поиска адресов
            user_location: Координаты пользователя для расчета расстояния и приоритизации
            limit: Максимальное количество результатов

        Returns:
            Список найденных адресов с координатами
        """
        async with Yandex(
            api_key=self.api_key,
            adapter_factory=AioHTTPAdapter,
            timeout=10,
        ) as geolocator:
            try:
                # Используем прямое геокодирование - поиск координат по адресу
                locations = await geolocator.geocode(query, exactly_one=False)

                if not locations:
                    return []

                # Ограничиваем количество результатов вручную
                if limit:
                    locations = locations[:limit]

                parsed_locations = []
                for location in locations:
                    parsed_location = await self._parse_location_from_raw(location)
                    if parsed_location:
                        # Если указано местоположение пользователя, рассчитываем расстояние
                        if user_location:
                            dist_km = self.calculate_distance(
                                Point(
                                    parsed_location.latitude, parsed_location.longitude
                                ),
                                user_location,
                            )
                            # Добавляем расстояние как дополнительное поле для сортировки
                            parsed_location.distance_km = dist_km

                        parsed_locations.append(parsed_location)

                # Сортируем по расстоянию, если есть координаты пользователя
                if user_location:
                    parsed_locations.sort(
                        key=lambda loc: getattr(loc, "distance_km", float("inf"))
                    )

                return parsed_locations

            except GeocoderInsufficientPrivileges as e:
                logger.error(
                    "Yandex geocoder API key is invalid or has insufficient privileges: %s",
                    e,
                    exc_info=True,
                )
                return []
            except GeocoderServiceError as e:
                logger.error("Yandex geocoder request failed: %s", e, exc_info=True)
                return []
            except Exception as e:
                logger.error("Failed to search addresses: %s", e, exc_info=True)
                return []

    @staticmethod
    def calculate_distance(
        point1: Point,
        point2: Point,
    ) -> float:
        """
        Расчет расстояния между двумя точками в километрах.

        Args:
            point1: Первая точка (latitude, longitude)
            point2: Вторая точка (latitude, longitude)

        Returns:
            Расстояние в километрах
        """
        try:
            return distance.distance(
                (point1.latitude, point1.longitude), (point2.latitude, point2.longitude)
            ).kilometers
        except Exception as e:
            logger.error("Failed to calculate distance: %s", e)
            return float("inf")

    async def find_nearest_delivery_points_by_address(
        self,
        address_query: str,
        delivery_points: list,  # Список уже полученных ПВЗ
        user_location: Point | None = None,
        target_location: Point | None = None,
        limit: int = 10,
    ) -> list:
        """
        Находит ближайшие ПВЗ к найденному адресу с учетом расстояния от пользователя.

        Логика:
        1. Если target_location не указан, геокодируем address_query в координаты
        2. Рассчитываем расстояние от каждого ПВЗ до целевого адреса
        3. Если указан user_location, учитываем и расстояние от пользователя
        4. Сортируем по удобству (близость к цели + расстояние от пользователя)

        Args:
            address_query: Адрес для поиска ближайших ПВЗ
            delivery_points: Список ПВЗ для фильтрации
            user_location: Координаты пользователя для дополнительной приоритизации
            target_location: Координаты целевого адреса (если уже известны)
            limit: Максимальное количество результатов

        Returns:
            Отсортированный список ПВЗ с расчетом расстояний
        """
        try:
            # Если координаты целевого адреса не переданы, находим их
            if not target_location:
                found_addresses = await self.search_addresses(address_query, limit=1)
                if not found_addresses:
                    logger.warning(f"Could not geocode address: {address_query}")
                    return []
                target_location = Point(
                    found_addresses[0].latitude, found_addresses[0].longitude
                )

            # Рассчитываем расстояния и добавляем метрики для каждого ПВЗ
            points_with_distance = []
            for point in delivery_points:
                # Получаем координаты ПВЗ
                point_location = Point(
                    point.location.latitude, point.location.longitude
                )

                # Расстояние от ПВЗ до целевого адреса
                distance_to_target = self.calculate_distance(
                    point_location, target_location
                )

                # Расстояние от пользователя до ПВЗ (если указано местоположение пользователя)
                distance_from_user = 0.0
                if user_location:
                    distance_from_user = self.calculate_distance(
                        point_location, user_location
                    )

                # Рассчитываем общий показатель удобства
                # Приоритет: близость к целевому адресу важнее, но учитываем и расстояние от пользователя
                convenience_score = distance_to_target + (distance_from_user * 0.3)

                points_with_distance.append(
                    {
                        "point": point,
                        "distance_to_target_km": distance_to_target,
                        "distance_from_user_km": distance_from_user,
                        "convenience_score": convenience_score,
                    }
                )

            # Сортируем по показателю удобства (меньше = лучше)
            points_with_distance.sort(key=lambda x: x["convenience_score"])

            # Возвращаем топ результатов с добавленной информацией о расстояниях
            result = []
            for item in points_with_distance[:limit]:
                point = item["point"]
                # Добавляем информацию о расстояниях как дополнительные поля
                if hasattr(point, "__dict__"):
                    point.distance_to_target_km = item["distance_to_target_km"]
                    point.distance_from_user_km = item["distance_from_user_km"]
                result.append(point)

            return result

        except Exception as e:
            logger.error("Failed to find nearest delivery points: %s", e)
            return []

    async def _parse_location_from_raw(
        self,
        location: Location,
    ) -> ParsedLocation | None:
        """
        Парсит Location объект в ParsedLocation для результатов прямого геокодирования.

        Args:
            location: Location объект от геокодера

        Returns:
            ParsedLocation объект или None при ошибке
        """
        try:
            if not location or not location.raw:
                return None

            geo_object = location.raw
            address_data = geo_object["metaDataProperty"]["GeocoderMetaData"]["Address"]
            components = self._parse_location_components(
                address_data.get("Components", [])
            )

            # Формируем адрес как "улица, дом" при наличии информации
            address_parts = []
            street = components.get("street")
            house = components.get("house")

            if street and street.strip():
                address_parts.append(street.strip())
            if house and house.strip():
                address_parts.append(house.strip())

            address = ", ".join(address_parts) if address_parts else None

            return ParsedLocation(
                country=components.get("country"),
                country_code=address_data.get("country_code"),
                region=components.get("province"),
                city=components.get("locality"),
                street=street,
                house=house,
                address=address,
                longitude=location.longitude,
                latitude=location.latitude,
            )
        except Exception as e:
            logger.error("Failed to parse location from raw data: %s", e)
            return None

    @staticmethod
    def _parse_location_components(components: list[dict]) -> dict:
        result = {}
        province_count = 0

        for component in components:
            kind = component["kind"]
            name = component["name"]

            if kind == "province":
                province_count += 1
                if province_count == 2:
                    result[kind] = name
            elif kind not in result:
                result[kind] = name

        return result

    async def get_location_by_point(
        self,
        point: Point,
    ) -> ParsedLocation | None:
        location = await self.reverse(point)
        if not location:
            return None

        geo_object = location.raw
        address: dict = geo_object["metaDataProperty"]["GeocoderMetaData"]["Address"]
        components = self._parse_location_components(address.get("Components"))

        return ParsedLocation(
            country=components.get("country"),
            country_code=address.get("country_code"),
            region=components.get("province"),
            city=components.get("locality"),
            street=components.get("street"),
            house=components.get("house"),
            address=address.get("formatted"),
            longitude=point.longitude,
            latitude=point.latitude,
        )
