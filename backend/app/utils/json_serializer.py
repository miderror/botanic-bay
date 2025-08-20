# backend/app/utils/json_serializer.py
import json
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class CustomJSONEncoder(json.JSONEncoder):
    """
    Кастомный JSON сериализатор для корректной обработки
    специфических типов данных (Decimal, datetime, UUID)
    """

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


def json_serializer(obj):
    """
    Функция для сериализации объектов в JSON

    Args:
        obj: Объект для сериализации

    Returns:
        str: JSON строка
    """
    return json.dumps(obj, cls=CustomJSONEncoder)
