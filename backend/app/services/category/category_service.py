# backend/app/services/category/category_service.py
from typing import List

from app.core.logger import logger
from app.crud.category import CategoryCRUD


class CategoryService:
    """Сервис для работы с категориями"""

    def __init__(self, category_crud: CategoryCRUD):
        self.category_crud = category_crud

    async def get_all_categories(self) -> List[str]:
        """
        Получение списка всех имен категорий

        Returns:
            List[str]: Список имен категорий
        """
        try:
            logger.debug("Fetching all categories from database")
            categories = await self.category_crud.get_all()

            # Дополнительное логирование типов данных
            logger.debug(f"Raw categories type: {type(categories)}")
            logger.debug(f"Raw categories content: {categories}")

            category_names = [
                category.name for category in categories if hasattr(category, "name")
            ]

            logger.info(
                "Retrieved all categories",
                extra={"count": len(category_names), "names": category_names},
            )

            return category_names
        except Exception as e:
            logger.error(f"Failed to get all categories: {str(e)}", exc_info=True)
            raise
