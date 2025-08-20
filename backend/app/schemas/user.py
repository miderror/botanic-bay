from datetime import date, datetime
from enum import Enum, StrEnum, auto
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class SUserBase(BaseModel):
    """Базовая схема пользователя"""

    telegram_id: Annotated[
        int, Field(..., description="Telegram ID пользователя", gt=0, strict=True)
    ]
    username: Optional[str] = Field(None, description="Username в Telegram")
    full_name: str = Field(..., description="Полное имя пользователя")


class SUserCreate(SUserBase):
    """Схема для создания пользователя"""

    referral_code: Optional[str] = None


class SUser(SUserBase):
    """Схема для отображения пользователя"""

    id: UUID
    referral_code: str
    is_active: bool
    roles: List[str] = Field(
        default_factory=list, description="Список ролей пользователя"
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SUserProfile(BaseModel):
    full_name: Optional[str] = Field(None, description="ФИО пользователя")
    phone_number: Optional[str] = Field(None, description="Номер телефона пользователя")
    email: Optional[str] = Field(None, description="Email пользователя")

    class Config:
        from_attributes = True


class SUserProfileUpdate(BaseModel):
    """Схема для обновления профиля пользователя"""

    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class SAuthData(BaseModel):
    """Схема данных инициализации Telegram WebApp"""

    auth_date: int = Field(..., description="Дата авторизации")
    hash: str = Field(..., description="Хеш для проверки подлинности данных")


class SInitData(BaseModel):
    """Схема данных инициализации от Telegram"""

    query_id: Optional[str] = Field(None, description="ID запроса")
    user: SUserBase
    auth_data: SAuthData
    start_param: Optional[str] = Field(None, description="Стартовый параметр")


class SAuthResponse(BaseModel):
    """Схема ответа при аутентификации"""

    user: SUser
    message: str = Field(
        "Authentication successful", description="Сообщение об успешной аутентификации"
    )
    status: str = Field("success", description="Статус аутентификации")

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "telegram_id": 123456789,
                    "username": "john_doe",
                    "full_name": "John Doe",
                    "referral_code": "ABC123",
                    "is_active": True,
                    "created_at": "2024-02-05T12:00:00",
                    "updated_at": "2024-02-05T12:00:00",
                },
                "message": "Authentication successful",
                "status": "success",
            }
        }


class SAuthError(BaseModel):
    """Схема ошибки аутентификации"""

    message: str = Field(..., description="Сообщение об ошибке")
    status: str = Field("error", description="Статус ошибки")
    error_code: str = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Invalid authentication data",
                "status": "error",
                "error_code": "AUTH_INVALID_DATA",
            }
        }


class UserDiscountLevel(StrEnum):
    BRONZE = auto()
    SILVER = auto()
    GOLD = auto()
    NONE = auto()


class SUserDiscountProgress(BaseModel):
    current_percent: float
    current_level: UserDiscountLevel
    current_total: float
    required_total: float
    amount_left: float
    next_level: UserDiscountLevel
    next_percent: float


class SUserMonthlyOrders(BaseModel):
    monthly_orders_amount: int
