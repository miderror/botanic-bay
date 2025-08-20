import logging
import sys
from pathlib import Path
from pprint import pformat

from app.core.settings import settings


class CustomFormatter(logging.Formatter):
    """Кастомный форматтер для логов с цветами для разных уровней и поддержкой extra параметров"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        # Применяем цвета к базовому сообщению
        color = self.COLORS.get(record.levelname, "")

        # Форматируем базовое сообщение
        base_message = super().format(record)

        # Получаем только пользовательские extra параметры
        # Исключаем стандартные атрибуты LogRecord
        extra_data = {}
        for key, value in record.__dict__.items():
            if (
                not key.startswith("_")
                and key not in logging.LogRecord.__dict__
                and key
                not in (
                    "args",
                    "asctime",
                    "created",
                    "exc_info",
                    "exc_text",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "msg",
                    "name",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "stack_info",
                    "thread",
                    "threadName",
                )
            ):
                extra_data[key] = value

        # Если есть extra параметры, форматируем их
        if extra_data:
            try:
                extra_formatted = pformat(extra_data, indent=2, width=80)
                extra_formatted = extra_formatted.replace("\n", "\n    ")
                full_message = f"{base_message}\n    Extra: {extra_formatted}"
            except Exception:
                full_message = f"{base_message}\n    Extra: {str(extra_data)}"
        else:
            full_message = base_message

        # Применяем цвет ко всему сообщению
        if color:
            return f"{color}{full_message}{self.RESET}"
        return full_message


def setup_logger(name: str = "app") -> logging.Logger:
    """
    Настройка логгера с кастомным форматированием

    Args:
        name: Имя логгера

    Returns:
        logging.Logger: Настроенный логгер
    """

    logger = logging.getLogger(name)

    # Устанавливаем уровень логирования из настроек
    logger.setLevel(settings.LOG_LEVEL)

    # Если у логгера уже есть хендлеры, не добавляем новые
    if logger.handlers:
        return logger

    # Создаем консольный хендлер
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Настраиваем форматирование
    formatter = CustomFormatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # Добавляем хендлер к логгеру
    logger.addHandler(console_handler)

    # Если определена директория для файловых логов
    if hasattr(settings, "LOGS_DIR"):
        logs_dir = Path(settings.LOGS_DIR)
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Создаем файловый хендлер
        file_handler = logging.FileHandler(logs_dir / f"{name}.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Используем такой же форматтер для файла, но без цветов
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)

        # Добавляем файловый хендлер
        logger.addHandler(file_handler)

    return logger


# Создаем глобальный логгер приложения
logger = setup_logger()
