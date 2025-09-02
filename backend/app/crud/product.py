from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.logger import logger
from app.models.category import Category
from app.models.product import Product
from app.schemas.product import SProductCreate, SProductUpdate


class ProductCRUD:
    """
    CRUD операции для работы с товарами
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_products(
        self, skip: int = 0, limit: int = 10, category: Optional[str] = None
    ) -> Tuple[List[Product], int]:
        """
        Получение списка активных товаров
        """
        query = (
            select(Product)
            .where(Product.is_active == True)
            .options(joinedload(Product.category))
        )

        if category:
            query = query.join(Product.category).where(Category.name == category)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        query = query.order_by(Product.name).offset(skip).limit(limit)
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
        """
        query = (
            select(Product)
            .where(Product.id == product_id)
            .options(joinedload(Product.category))
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
        """
        try:
            product_dict = product_data.model_dump(exclude_unset=True)

            if category_name := product_dict.pop("category", None):
                from app.crud.category import CategoryCRUD

                category_crud = CategoryCRUD(self.session)
                category = await category_crud.get_or_create(category_name)
                product_dict["category_id"] = category.id

            product_dict.pop("additional_images_urls", None)

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
        Обновление товара с умной обработкой файловых полей, чтобы избежать перезаписи.
        """
        product = await self.get_product(product_id)
        if not product:
            return None

        update_data = product_data.model_dump(exclude_unset=True)

        try:
            if "category" in update_data:
                category_name = update_data.pop("category")
                if category_name:
                    from app.crud.category import CategoryCRUD

                    category_crud = CategoryCRUD(self.session)
                    category = await category_crud.get_or_create(category_name)
                    product.category_id = category.id
                else:
                    product.category_id = None

            image_fields = ["image_url", "background_image_url", "header_image_url"]
            for field in image_fields:
                if field in update_data:
                    new_value = update_data.pop(field)

                    if new_value is not None and not isinstance(new_value, UploadFile):
                        logger.debug(
                            f"Ignoring invalid/empty update for image field '{field}'."
                        )
                        continue

                    setattr(product, field, new_value)

            for key, value in update_data.items():
                setattr(product, key, value)

            await self.session.commit()
            await self.session.refresh(product)

            logger.info(
                "Updated product",
                extra={
                    "product_id": str(product_id),
                    "updated_fields": list(
                        product_data.model_dump(exclude_unset=True).keys()
                    ),
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
            "header_image_url": product.header_image_url,
            "sku": product.sku,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
        }

    async def get_products_with_pagination(
        self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Product], int]:
        """
        Получение списка АКТИВНЫХ товаров с пагинацией и фильтрацией
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
        """
        product = await self.get_product(product_id)
        if not product:
            return False

        await self.session.delete(product)
        await self.session.commit()
        logger.info("Product deleted", extra={"product_id": str(product_id)})
        return True

    async def update_product_images(
        self, product_id: UUID, image_data: dict
    ) -> Optional[Product]:
        """
        Обновление изображений товара. (Устаревший метод)
        """
        logger.warning(
            "`update_product_images` is deprecated. Use `update_product` instead."
        )
        update_schema = SProductUpdate(**image_data)
        return await self.update_product(product_id, update_schema)

    async def search_products(
        self, search_query: str, skip: int = 0, limit: int = 10
    ) -> tuple[List[Product], int]:
        """
        Поиск товаров по названию среди АКТИВНЫХ товаров
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
                .options(joinedload(Product.category))
            )

            count_query = select(func.count()).select_from(query.subquery())
            total = await self.session.scalar(count_query)

            query = query.order_by(Product.name).offset(skip).limit(limit)

            result = await self.session.execute(query)
            products = result.unique().scalars().all()

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
