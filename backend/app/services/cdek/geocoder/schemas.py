from pydantic import BaseModel


class ParsedLocation(BaseModel):
    address: str | None = None
    country_code: str
    country: str
    region: str | None = None
    sub_region: str | None = None
    city: str | None = None
    street: str | None = None
    house: str | None = None
    longitude: float
    latitude: float
    bbox: list[float] | None = None
    # Расстояние в километрах (для результатов поиска)
    distance_km: float | None = None

    @property
    def address_full(self) -> str:
        """Полный адрес, собранный из компонентов."""
        parts = [
            self.country,
            self.region,
            self.sub_region,
            self.city,
            self.address,
        ]
        return ", ".join(filter(None, parts))
