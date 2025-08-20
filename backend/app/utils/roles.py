# backend/app/utils/roles.py
from functools import wraps

from fastapi import HTTPException, status

from app.core.constants import UserRoles


def check_role(required_role: str):
    """Decorator to check if user has required role"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if not user or not user.has_role(required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def is_admin(user) -> bool:
    """Check if user is admin"""
    return user.has_role(UserRoles.ADMIN.value)


def is_manager(user) -> bool:
    """Check if user is manager"""
    return user.has_role(UserRoles.MANAGER.value)
