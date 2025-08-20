# backend/app/services/telegram/interfaces.py
from abc import ABC, abstractmethod

from aiogram import Bot, Dispatcher


class ITelegramBot(ABC):
    """
    Интерфейс для работы с Telegram ботом
    Позволяет абстрагировать логику работы от конкретной реализации (webhook/polling)
    """

    @abstractmethod
    async def start(self) -> None:
        """Запуск бота"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Остановка бота"""
        pass

    @property
    @abstractmethod
    def bot(self) -> Bot:
        """Получение экземпляра бота"""
        pass

    @property
    @abstractmethod
    def dispatcher(self) -> Dispatcher:
        """Получение экземпляра диспетчера"""
        pass
