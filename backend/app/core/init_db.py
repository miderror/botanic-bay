# backend/app/core/init_db.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.constants import UserRoles
from app.core.logger import logger
from app.models.user import Role


async def init_roles(db: AsyncSession) -> None:
    """Initialize default roles in the system"""
    logger.debug("Starting roles initialization...")

    # Получаем существующие роли
    result = await db.execute(select(Role))
    existing_roles = result.scalars().all()
    existing_role_names = {role.name for role in existing_roles}

    logger.debug(f"Found existing roles: {existing_role_names}")

    default_roles = UserRoles.get_default_roles()
    logger.debug(f"Default roles to create: {default_roles}")

    # Создаем недостающие роли
    created_roles = []
    for role_name, description in default_roles.items():
        if role_name not in existing_role_names:
            role = Role(name=role_name, description=description)
            db.add(role)
            created_roles.append(role_name)
            logger.debug(f"Adding new role: {role_name} - {description}")

    if created_roles:
        await db.commit()
        logger.info(f"Successfully created roles: {created_roles}")
    else:
        logger.info("No new roles needed to be created")

    logger.debug("Roles initialization completed")
