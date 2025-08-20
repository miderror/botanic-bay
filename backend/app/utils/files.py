# backend/app/utils/files.py
import os
import uuid
from typing import Optional

from fastapi import UploadFile

from app.core.logger import logger
from app.core.settings import settings


async def save_upload_file(
    upload_file: UploadFile, subfolder: str = ""
) -> Optional[str]:
    """
    Сохраняет загруженный файл в MEDIA_DIR

    Args:
        upload_file: Загруженный файл
        subfolder: Подпапка в MEDIA_DIR для сохранения

    Returns:
        Optional[str]: URL для доступа к файлу или None при ошибке
    """
    try:
        # Создаем уникальное имя файла
        ext = os.path.splitext(upload_file.filename)[1].lower()
        filename = f"{uuid.uuid4()}{ext}"

        # Создаем путь для сохранения
        relative_path = f"{subfolder}/{filename}" if subfolder else filename
        save_path = settings.MEDIA_ROOT / relative_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Сохраняем файл
        content = await upload_file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        # Возвращаем URL для доступа к файлу
        return f"{settings.MEDIA_URL}{relative_path}"

    except Exception as e:
        logger.error("Failed to save uploaded file", exc_info=True)
        return None


def delete_file(file_path: str) -> bool:
    """
    Удаляет файл из MEDIA_DIR

    Args:
        file_path: Относительный путь к файлу

    Returns:
        bool: True если файл успешно удален
    """
    try:
        full_path = settings.MEDIA_DIR / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    except Exception as e:
        logger.error("Failed to delete file", exc_info=True)
        return False
