# backend/app/crud/category.py
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.models.category import Category


class CategoryCRUD:
    """CRUD операции для работы с категориями"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, name: str) -> Category:
        """
        Получает существующую категорию или создает новую

        Args:
            name: Название категории

        Returns:
            Category: Объект категории
        """
        query = select(Category).where(Category.name == name)
        result = await self.session.execute(query)
        category = result.scalar_one_or_none()

        if not category:
            logger.info(f"Creating new category: {name}")
            category = Category(name=name)
            self.session.add(category)
            await self.session.commit()

        return category

    async def get_all(self) -> List[Category]:
        """
        Получение списка всех категорий

        Returns:
            List[Category]: Список категорий
        """
        result = await self.session.execute(select(Category))
        return result.scalars().all()
