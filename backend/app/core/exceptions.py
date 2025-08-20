"""Кастомные исключения приложения."""


class AppError(Exception):
    """Базовое исключение приложения."""

    pass


class UserAddressNotFoundError(AppError):
    """Пользователь не найден в базе данных."""

    pass


class UserAddressUpdateError(AppError):
    """Ошибка при обновлении адреса пользователя."""

    pass
