# backend/app/utils/json_helpers.py
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


def serialize_for_json(obj: Any) -> Any:
    """
    Рекурсивно преобразует все специальные типы в объектах Python
    в типы, которые можно сериализовать в JSON

    Обрабатывает:
    - Decimal -> float
    - datetime/date -> строка ISO формата
    - UUID -> строка
    - вложенные словари и списки

    Args:
        obj: Объект для сериализации

    Returns:
        Any: Объект, готовый для сериализации в JSON
    """
    if isinstance(obj, dict):
        # Рекурсивно обрабатываем каждый элемент словаря
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Рекурсивно обрабатываем каждый элемент списка
        return [serialize_for_json(i) for i in obj]
    elif isinstance(obj, Decimal):
        # Преобразуем Decimal в float
        return float(obj)
    elif isinstance(obj, (datetime, date)):
        # Преобразуем дату/время в ISO строку
        return obj.isoformat()
    elif isinstance(obj, UUID):
        # Преобразуем UUID в строку
        return str(obj)

    # Возвращаем объект без изменений, если он уже сериализуемый
    return obj
