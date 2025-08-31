from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.logger import logger
from app.models.category import Category
from app.models.product import Product
from app.schemas.product import SProductCreate, SProductUpdate


class ProductCRUD:
    """
    CRUD операции для работы с товарами
    """

    def __init__(self, session: AsyncSession):
        """
        Инициализация CRUD операций

        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session

    async def get_products(
        self, skip: int = 0, limit: int = 10, category: Optional[str] = None
    ) -> Tuple[List[Product], int]:
        """
        Получение списка активных товаров

        Args:
            skip: Сколько записей пропустить
            limit: Сколько записей вернуть
            category: Название категории для фильтрации

        Returns:
            Tuple[List[Product], int]: Список активных товаров и общее количество
        """
        query = (
            select(Product)
            .where(Product.is_active == True)
            .options(
                selectinload(Product.additional_images), joinedload(Product.category)
            )
        )

        if category:
            query = query.join(Product.category).where(Category.name == category)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        products = result.unique().scalars().all()

        logger.debug(
            "Active products query result",
            extra={
                "products_count": len(products),
                "total": total,
                "category_filter": category,
            },
        )

        return products, total

    async def get_product(self, product_id: UUID) -> Optional[Product]:
        """
        Получение товара по ID

        Args:
            product_id: ID товара

        Returns:
            Optional[Product]: Товар если найден, иначе None
        """
        query = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.additional_images), joinedload(Product.category)
            )
        )
        result = await self.session.execute(query)
        product = result.scalar_one_or_none()

        if product:
            logger.debug(f"Retrieved product", extra={"product_id": str(product_id)})
        else:
            logger.debug(f"Product not found", extra={"product_id": str(product_id)})

        return product

    async def create_product(self, product_data: SProductCreate) -> Product:
        """
        Создание нового товара

        Args:
            product_data: Данные товара

        Returns:
            Product: Созданный товар
        """
        try:
            product_dict = product_data.model_dump()

            if category_name := product_dict.pop("category", None):
                from app.crud.category import CategoryCRUD

                category_crud = CategoryCRUD(self.session)
                category = await category_crud.get_or_create(category_name)
                product_dict["category"] = category

            product = Product(**product_dict)
            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)

            logger.info(
                "Created new product",
                extra={
                    "product_id": str(product.id),
                    "product_name": product.name,
                    "category": product.category_name,
                },
            )

            return product

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to create product", exc_info=True)
            raise

    async def update_product(
        self, product_id: UUID, product_data: SProductUpdate
    ) -> Optional[Product]:
        """
        Обновление товара
        """
        update_data = product_data.model_dump(exclude_unset=True)

        if "additional_images_urls" in update_data:
            if not product_data.additional_images_urls:
                update_data["additional_images_urls"] = []

        if "category" in update_data:
            category_name = update_data["category"]
            if category_name:
                from app.crud.category import CategoryCRUD

                category_crud = CategoryCRUD(self.session)
                category = await category_crud.get_or_create(category_name)
                update_data["category_id"] = category.id
            else:
                update_data["category_id"] = None
            del update_data["category"]

        query = (
            update(Product)
            .where(Product.id == product_id)
            .values(**update_data)
            .returning(Product)
        )

        try:
            result = await self.session.execute(query)
            product = result.scalar_one_or_none()

            if product:
                await self.session.commit()
                await self.session.refresh(product)
                logger.info(
                    "Updated product",
                    extra={
                        "product_id": str(product_id),
                        "updated_fields": list(update_data.keys()),
                    },
                )

            return product
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update product", exc_info=True)
            raise

    def to_dict(self, product: Product) -> dict:
        """
        Преобразование Product в словарь для API

        Args:
            product: Объект продукта

        Returns:
            dict: Словарь с данными продукта
        """
        return {
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "additional_description": product.additional_description,
            "price": float(product.price),
            "stock": product.stock,
            "is_active": product.is_active,
            "category": product.category.name if product.category else None,
            "image_url": product.image_url,
            "background_image_url": product.background_image_url,
            "additional_images_urls": product.additional_images_urls or [],
            "sku": product.sku,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
        }

    async def get_products_with_pagination(
        self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Product], int]:
        """
        Получение списка АКТИВНЫХ товаров с пагинацией и фильтрацией

        Args:
            skip: Сколько записей пропустить
            limit: Сколько записей вернуть
            filters: Словарь с фильтрами вида {"поле": "значение"}

        Returns:
            Tuple[List[Product], int]: Список товаров и общее количество
        """
        query = select(Product).where(Product.is_active == True)

        if filters:
            if name := filters.get("name"):
                query = query.where(Product.name.ilike(f"%{name}%"))
            if category := filters.get("category"):
                query = query.join(Product.category).where(Category.name == category)
            if min_price := filters.get("min_price"):
                query = query.where(Product.price >= min_price)
            if max_price := filters.get("max_price"):
                query = query.where(Product.price <= max_price)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        products = result.scalars().all()

        logger.debug(
            "Retrieved active products with pagination",
            extra={"total": total, "skip": skip, "limit": limit, "filters": filters},
        )

        return products, total

    async def delete_product(self, product_id: UUID) -> bool:
        """
        Удаление товара

        Args:
            product_id: ID товара

        Returns:
            bool: True если удален, False если не найден
        """
        query = select(Product).where(Product.id == product_id)
        result = await self.session.execute(query)
        product = result.scalar_one_or_none()

        if not product:
            return False

        await self.session.delete(product)
        await self.session.commit()

        logger.info("Product deleted", extra={"product_id": str(product_id)})
        return True

    async def update_product_images(
        self, product_id: UUID, additional_images_urls: List[str]
    ) -> Optional[Product]:
        """
        Обновление дополнительных изображений товара

        Args:
            product_id: ID товара
            additional_images_urls: Список URL дополнительных изображений

        Returns:
            Optional[Product]: Обновленный товар или None если не найден
        """
        try:
            query = (
                update(Product)
                .where(Product.id == product_id)
                .values(additional_images_urls=additional_images_urls)
                .returning(Product)
            )

            result = await self.session.execute(query)
            product = result.scalar_one_or_none()

            if product:
                await self.session.commit()
                logger.info(
                    "Updated product additional images",
                    extra={
                        "product_id": str(product_id),
                        "images_count": len(additional_images_urls),
                    },
                )

            return product

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update product images", exc_info=True)
            raise

    async def search_products(
        self, search_query: str, skip: int = 0, limit: int = 10
    ) -> tuple[List[Product], int]:
        """
        Поиск товаров по названию среди АКТИВНЫХ товаров

        Args:
            search_query: Поисковый запрос
            skip: Сколько записей пропустить
            limit: Сколько записей вернуть

        Returns:
            Tuple[List[Product], int]: Список найденных активных товаров и общее количество
        """
        try:
            query = (
                select(Product)
                .where(
                    and_(
                        Product.name.ilike(f"%{search_query}%"),
                        Product.is_active == True,
                    )
                )
                .options(
                    selectinload(Product.additional_images),
                    joinedload(Product.category),
                )
            )

            count_query = select(func.count()).select_from(query.subquery())
            total = await self.session.scalar(count_query)

            query = query.offset(skip).limit(limit)

            result = await self.session.execute(query)
            products = result.scalars().all()

            logger.debug(
                "Product search completed",
                extra={
                    "query": search_query,
                    "active_results_count": len(products),
                    "total_active_matches": total,
                    "skip": skip,
                    "limit": limit,
                },
            )

            return products, total

        except Exception as e:
            logger.error(
                "Failed to search products",
                extra={"query": search_query},
                exc_info=True,
            )
            raise
