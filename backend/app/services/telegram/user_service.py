from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.constants import UserRoles
from app.core.logger import logger
from app.crud.user import UserCRUD
from app.models.user import Role, User
from app.schemas.user import SUserCreate
from app.services.referral.referral_service import ReferralService


class TelegramUserService:
    """Сервис для работы с пользователями Telegram"""

    def __init__(self, session: AsyncSession, referral_service: ReferralService):
        self.session = session
        self.user_crud = UserCRUD(session)
        self.referral_service = referral_service

    async def get_or_create_role(self, role_name: str) -> Role:
        """
        Получение роли по имени или создание новой

        Args:
            role_name: Название роли

        Returns:
            Role: Объект роли
        """
        query = select(Role).where(Role.name == role_name)
        result = await self.session.execute(query)
        role = result.scalar_one_or_none()

        if not role:
            logger.info(f"Creating new role: {role_name}")
            role = Role(name=role_name)
            self.session.add(role)
            await self.session.commit()

        return role

    async def register_user(
        self,
        telegram_id: int,
        username: str,
        full_name: str,
        referral_code: str = None,
    ) -> User:
        """
        Регистрация нового пользователя или получение существующего

        Args:
            telegram_id: ID пользователя в Telegram
            username: Имя пользователя
            full_name: Полное имя
            referral_code: Код приглашения реферрера

        Returns:
            User: Объект пользователя
        """
        # Проверяем существование пользователя
        existing_user = await self.user_crud.get_by_telegram_id(telegram_id)

        if existing_user:
            logger.info(
                "User already registered",
                extra={"telegram_id": telegram_id, "username": username},
            )
            return existing_user

        # Создаем нового пользователя
        user_data = SUserCreate(
            telegram_id=telegram_id, username=username, full_name=full_name
        )

        user = await self.user_crud.create(user_data)

        # Добавляем базовую роль пользователя
        role = await self.get_or_create_role(UserRoles.USER.value)
        user.roles.append(role)
        await self.session.commit()

        if referral_code:
            referrer = await self.user_crud.get_by_referral_code(referral_code)
            if referrer is not None:
                await self.referral_service.save_referral(referrer.id, user.id)

        logger.info(
            "User successfully registered with default role",
            extra={
                "telegram_id": user.telegram_id,
                "username": user.username,
                "role": UserRoles.USER.value,
            },
        )

        return user
