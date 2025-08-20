# app/schemas/export.py
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.order import SOrderFilter


class ExportFormat(str, Enum):
    """Форматы экспорта данных"""

    CSV = "csv"
    EXCEL = "excel"


class SExportOrdersRequest(BaseModel):
    """Схема запроса на экспорт заказов"""

    format: ExportFormat = Field(..., description="Формат экспорта (csv или excel)")
    filters: Optional[SOrderFilter] = Field(
        None, description="Фильтры для экспорта заказов"
    )
