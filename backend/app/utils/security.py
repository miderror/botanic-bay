# backend/app/utils/security.py
import random
import string

from app.core.logger import logger


def generate_referral_code(length: int = 8) -> str:
    """
    Генерирует уникальный реферальный код заданной длины

    Args:
        length: Длина генерируемого кода (по умолчанию 8 символов)

    Returns:
        str: Сгенерированный реферальный код

    Example:
        >>> generate_referral_code()
        'A7B2C9D4'
    """
    # Используем только заглавные буквы и цифры для лучшей читаемости
    characters = string.ascii_uppercase + string.digits

    # Генерируем код
    referral_code = "".join(random.choice(characters) for _ in range(length))

    logger.debug(f"Generated new referral code: {referral_code}")
    return referral_code
