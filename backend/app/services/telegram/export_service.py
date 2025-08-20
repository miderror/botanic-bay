# backend/app/services/telegram/export_service.py

from typing import Dict, Optional

from app.core.logger import logger
from app.schemas.export import ExportFormat
from app.services.export.export_service import ExportService
from app.services.telegram.bot_manager import TelegramBotManager


class TelegramExportService:
    """Сервис для экспорта данных через Telegram бота"""

    def __init__(self, export_service: ExportService, bot_manager: TelegramBotManager):
        self.export_service = export_service
        self.bot_manager = bot_manager

    async def export_orders_to_telegram(
        self, chat_id: int, export_format: ExportFormat, filters: Optional[Dict] = None
    ) -> bool:
        """
        Экспорт заказов через Telegram бота

        Args:
            chat_id: ID чата/пользователя Telegram
            export_format: Формат экспорта (CSV/Excel)
            filters: Фильтры для выборки заказов

        Returns:
            bool: True если экспорт успешен, иначе False
        """
        try:
            # Получаем буфер с данными
            buffer, file_name, _ = await self.export_service.export_orders(
                export_format=export_format, filters=filters
            )

            # Преобразуем буфер в bytes для отправки
            buffer.seek(0)  # Убедимся, что указатель в начале буфера
            file_content = buffer.read()  # Прочитаем весь буфер

            # Убеждаемся, что у нас байты для отправки
            # Важно: проверяем только для CSV, так как Excel уже возвращается в байтах
            if export_format.value == "csv" and isinstance(file_content, str):
                file_content = file_content.encode("utf-8")

            # Проверка размера файла
            file_size_mb = len(file_content) / (1024 * 1024)
            if (
                file_size_mb > 50
            ):  # Телеграм ограничивает размер файлов до 50 МБ для ботов
                logger.warning(
                    f"File is too large for Telegram: {file_size_mb:.2f} MB",
                    extra={
                        "chat_id": chat_id,
                        "export_file_name": file_name,
                        "file_size_mb": file_size_mb,
                    },
                )
                return False

            # Безопасная диагностика формата файла
            try:
                preview = (
                    file_content[:100].hex()
                    if hasattr(file_content, "hex")
                    else str(file_content[:100])
                )
                logger.debug(
                    "File content preview",
                    extra={
                        "preview_bytes": preview,
                        "content_type": type(file_content).__name__,
                        "total_size": len(file_content),
                        "export_file_name": file_name,
                    },
                )
            except Exception as preview_err:
                logger.warning(f"Could not generate preview: {preview_err}")

            # Отправляем файл через бота
            result = await self.bot_manager.send_file(
                chat_id=chat_id,
                file_content=file_content,
                file_name=file_name,
                caption=f"Экспорт заказов ({export_format.value.upper()})",
            )

            if result:
                logger.info(
                    "File successfully exported to Telegram",
                    extra={
                        "chat_id": chat_id,
                        "export_file_name": file_name,
                        "format": export_format.value,
                        "file_size": len(file_content),
                    },
                )

            return result

        except Exception as e:
            logger.error(
                f"Error exporting orders to Telegram: {str(e)}",
                extra={
                    "chat_id": chat_id,
                    "format": export_format.value,
                    "error": str(e),
                },
            )
            return False
