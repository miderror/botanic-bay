# backend/app/crud/user.py
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.constants import UserRoles
from app.core.logger import logger
from app.models.user import Role, User
from app.schemas.user import SUserCreate
from app.utils.security import generate_referral_code


class UserCRUD:
    """Класс для операций с пользователями в БД"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Получение пользователя по Telegram ID с предзагрузкой ролей

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            Optional[User]: Найденный пользователь или None
        """
        # Добавляем joinedload для загрузки ролей вместе с пользователем
        query = (
            select(User)
            .options(joinedload(User.roles))
            .where(User.telegram_id == telegram_id)
        )
        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_referral_code(self, referral_code: str) -> Optional[User]:
        """
        Получение пользователя по Referral Code

        Args:
            referral_code: Код приглашения пользователя

        Returns:
            Optional[User]: Найденный пользователь или None
        """
        # Добавляем joinedload для загрузки ролей вместе с пользователем
        query = (
            select(User)
            .options(joinedload(User.roles))
            .where(User.referral_code == referral_code)
        )
        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()

    # backend/app/crud/user.py
    async def create(self, user_data: SUserCreate) -> User:
        """
        Создание нового пользователя

        Args:
            user_data: Данные для создания пользователя

        Returns:
            User: Созданный пользователь
        """
        # Генерируем уникальный реферальный код
        referral_code = generate_referral_code()

        # Создаем объект пользователя
        db_user = User(
            telegram_id=user_data.telegram_id,
            username=user_data.username,
            full_name=user_data.full_name,
            referral_code=referral_code,
        )

        # Получаем роль пользователя
        query = select(Role).where(Role.name == UserRoles.USER.value)
        result = await self.session.execute(query)
        role = result.scalar_one_or_none()

        if not role:
            # Создаем роль, если её нет
            role = Role(name=UserRoles.USER.value, description="Regular user")
            self.session.add(role)
            await self.session.flush()

        # Добавляем роль пользователю
        db_user.roles.append(role)

        # Сохраняем пользователя
        self.session.add(db_user)
        await self.session.commit()

        # После создания пользователя, перезагружаем его с ролями
        await self.session.refresh(db_user, ["roles"])

        logger.info(
            "New user created",
            extra={
                "telegram_id": db_user.telegram_id,
                "username": db_user.username,
                "roles": [role.name for role in db_user.roles],
            },
        )
        return db_user
