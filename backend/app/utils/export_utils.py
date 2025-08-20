# app/utils/export_utils.py
import csv
import io
from typing import Any, Dict, List

import pandas as pd

from app.core.logger import logger


def generate_csv(data: List[Dict[str, Any]], headers: Dict[str, str]) -> io.StringIO:
    """
    Генерация CSV файла из данных

    Args:
        data: Список словарей с данными
        headers: Словарь соответствия ключей заголовкам

    Returns:
        io.StringIO: Буфер с CSV данными
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(headers.keys()))

    # Записываем заголовки
    writer.writerow(headers)

    # Записываем данные
    for row in data:
        writer.writerow(row)

    output.seek(0)
    logger.info(f"Generated CSV file with {len(data)} rows")
    return output


def generate_excel(data: List[Dict[str, Any]], headers: Dict[str, str]) -> io.BytesIO:
    """
    Генерация Excel файла из данных

    Args:
        data: Список словарей с данными
        headers: Словарь соответствия ключей заголовкам

    Returns:
        io.BytesIO: Буфер с Excel данными
    """
    # Создаем DataFrame из данных
    df = pd.DataFrame(data)

    # Переименовываем колонки в соответствии с заголовками
    df = df.rename(columns=headers)

    # Записываем в буфер
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Orders")

    output.seek(0)
    logger.info(f"Generated Excel file with {len(data)} rows")
    return output
