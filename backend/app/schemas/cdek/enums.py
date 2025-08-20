from enum import Enum, StrEnum, auto


class UpperStrEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        return name


class CDEKCacheKey(StrEnum):
    REGIONS = "regions"
    CITIES = "cities"
    DELIVERY_POINTS = "delivery_points"


class OfficeType(UpperStrEnum):
    POSTAMAT = auto()
    PVZ = auto()
    ALL = auto()


class ContragentType(UpperStrEnum):
    LEGAL_ENTITY = auto()
    INDIVIDUAL = auto()


class TariffType(int, Enum):
    PARCEL_STORAGE_TO_STORAGE = 136
    PARCEL_STORAGE_TO_DOOR = 137
    PARCEL_DOOR_TO_STORAGE = 138
    PARCEL_DOOR_TO_DOOR = 139
    PARCEL_STORAGE_TO_POSTAMAT = 368


class DeliveryMode(int, Enum):
    DOOR_TO_DOOR = 1
    DOOR_TO_WAREHOUSE = 2
    WAREHOUSE_TO_DOOR = 3
    WAREHOUSE_TO_WAREHOUSE = 4


class RequestType(UpperStrEnum):
    CREATE = auto()
    UPDATE = auto()
    DELETE = auto()
    AUTH = auto()
    GET = auto()
    CREATE_CLIENT_RETURN = auto()


class RequestState(UpperStrEnum):
    ACCEPTED = auto()
    WAITING = auto()
    SUCCESSFUL = auto()
    INVALID = auto()


class PaymentType(UpperStrEnum):
    CASH = auto()
    CARD = auto()


class WebhookType(UpperStrEnum):
    ORDER_STATUS = auto()
    ORDER_MODIFIED = auto()
    PRINT_FORM = auto()
    RECEIPT = auto()
    DOWNLOAD_PHOTO = auto()
    PREALERT_CLOSED = auto()
    ACCOMPANYING_WAYBILL = auto()
    OFFICE_AVAILABILITY = auto()
    DELIV_PROBLEM = auto()
    DELIV_AGREEMENT = auto()


class OrderType(UpperStrEnum):
    DIRECT_ORDER = "direct_order"
    CLIENT_DIRECT_ORDER = "client_direct_order"


class ModificationType(UpperStrEnum):
    PLANED_DELIVERY_DATE_CHANGED = auto()
    DELIVERY_SUM_CHANGED = auto()
    DELIVERY_MODE_CHANGED = auto()


class ModificationNewValueType(UpperStrEnum):
    DATE = auto()
    FLOAT = auto()
    INTEGER = auto()
