# backend/app/services/telegram/bot_manager.py
import logging
from typing import Optional

from aiogram import Bot, Dispatcher

from app.core.logger import logger
from app.core.settings import settings

from .handlers import router
from .interfaces import ITelegramBot


class TelegramBotManager(ITelegramBot):
    """
    Менеджер для управления Telegram ботом
    Поддерживает режимы работы через webhook и polling
    """

    def __init__(self, token: Optional[str] = None):
        """
        Инициализация менеджера бота

        Args:
            token: Токен бота (опционально, если не указан - берется из настроек)
        """
        self._token = token or settings.TELEGRAM_BOT_TOKEN
        self._bot: Optional[Bot] = None
        self._dispatcher: Optional[Dispatcher] = None
        self._is_setup = False  # Флаг, указывающий, был ли уже настроен бот
        logger.info("Initializing Telegram bot manager")

    async def setup(self):
        """Настройка бота"""
        if self._is_setup:
            logger.info("Bot already setup, skipping")
            return

        try:
            # Проверка соединения с Telegram API остается
            import aiohttp
            from aiohttp import ClientSession, TCPConnector

            # Создать минимальную конфигурацию для бота
            self._bot = Bot(token=self._token)
            self._dispatcher = Dispatcher()

            aiogram_logger = logging.getLogger("aiogram")
            aiogram_logger.setLevel(logger.level)

            for handler in logger.handlers:
                aiogram_logger.addHandler(handler)
            aiogram_logger.propagate = True

            self._dispatcher.include_router(router)

            self._is_setup = True
            logger.info("Bot setup completed")
        except Exception as e:
            logger.error(f"Error during bot setup: {str(e)}")
            raise

    async def start(self) -> None:
        """Запуск бота"""
        await self.setup()
        logger.info("Starting bot in polling mode")
        await self._dispatcher.start_polling(self._bot)

    async def stop(self) -> None:
        """Остановка бота"""
        if self._bot:
            await self._bot.session.close()
            logger.info("Bot stopped")

    @property
    def bot(self) -> Bot:
        if not self._bot:
            raise RuntimeError("Bot is not initialized")
        return self._bot

    @property
    def dispatcher(self) -> Dispatcher:
        if not self._dispatcher:
            raise RuntimeError("Dispatcher is not initialized")
        return self._dispatcher

    async def send_file(
        self, chat_id: int, file_content: bytes, file_name: str, caption: str = None
    ) -> bool:
        """
        Отправка файла пользователю через бота

        Args:
            chat_id: ID чата/пользователя
            file_content: Содержимое файла в байтах
            file_name: Имя файла
            caption: Подпись к файлу (опционально)

        Returns:
            bool: True если отправка успешна, иначе False
        """
        try:
            from aiogram.types import BufferedInputFile

            # Проверка размера файла
            file_size_mb = len(file_content) / (1024 * 1024)
            if file_size_mb > 50:
                logger.warning(
                    f"File size ({file_size_mb:.2f} MB) exceeds Telegram limit (50 MB)",
                    extra={
                        "chat_id": chat_id,
                        "file_name": file_name,
                        "file_size_mb": file_size_mb,
                    },
                )
                return False

            # Создаем объект файла из байтов с явным указанием параметров
            input_file = BufferedInputFile(file=file_content, filename=file_name)

            # Отправляем файл с механизмом повторных попыток
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    await self.bot.send_document(
                        chat_id=chat_id,
                        document=input_file,
                        caption=caption or f"Экспорт данных: {file_name}",
                    )

                    logger.info(
                        "File sent successfully via bot",
                        extra={
                            "chat_id": chat_id,
                            "file_name": file_name,
                            "file_size_bytes": len(file_content),
                            "file_size_mb": file_size_mb,
                            "attempt": attempt,
                        },
                    )

                    return True

                except Exception as e:
                    if attempt < max_attempts:
                        import asyncio

                        retry_delay = (
                            attempt * 2
                        )  # Увеличиваем задержку с каждой попыткой

                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed, retrying in {retry_delay}s: {str(e)}",
                            extra={
                                "chat_id": chat_id,
                                "file_name": file_name,
                                "error": str(e),
                                "attempt": attempt,
                            },
                        )

                        await asyncio.sleep(retry_delay)
                    else:
                        # Если все попытки не удались, пробрасываем последнюю ошибку
                        raise

        except Exception as e:
            logger.error(
                f"Failed to send file via bot: {str(e)}",
                extra={
                    "chat_id": chat_id,
                    "file_name": file_name,
                    "error_details": str(e),
                },
            )
            return False
