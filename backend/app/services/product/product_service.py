# app/services/product/product_service.py
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status

from app.core.logger import logger
from app.crud.product import ProductCRUD
from app.models.product import Product
from app.services.cart.cart_service import CartService


class ProductService:
    def __init__(self, product_crud: ProductCRUD, cart_service: CartService):
        self.product_crud = product_crud
        self.cart_service = cart_service

    async def get_products(
        self, skip: int = 0, limit: int = 10, category: Optional[str] = None
    ) -> Tuple[List[Product], int]:
        """
        Получение списка активных товаров с реальным доступным количеством

        Args:
            skip: Сколько записей пропустить
            limit: Сколько записей вернуть
            category: Фильтр по категории

        Returns:
            Tuple[List[Product], int]: Список товаров и общее количество
        """
        # Получаем продукты через CRUD
        products, total = await self.product_crud.get_products(skip, limit, category)

        # Для каждого продукта считаем реальное доступное количество
        for product in products:
            available = await self.cart_service.get_available_quantity(product.id)

            # Добавляем свойство, не меняя оригинальное значение stock
            setattr(product, "available_quantity", available)

            logger.debug(
                "Calculated product availability",
                extra={
                    "product_id": str(product.id),
                    "total_stock": product.stock,
                    "available": available,
                },
            )

        # Добавляем отладку
        # for product in products:
        #     logger.debug("Product in service layer (-):", extra={
        #         "id": str(product.id),
        #         "name_": product.name,
        #         "background_image": product.background_image_url,
        #         "dict_repr": self.product_crud.to_dict(product)
        #     })

        return products, total

    async def get_product_details(self, product_id: UUID) -> Product:
        """
        Получение детальной информации о товаре с учетом доступного количества

        Args:
            product_id: ID товара

        Returns:
            Product: Информация о товаре с доступным количеством

        Raises:
            HTTPException: Если товар не найден
        """
        product = await self.product_crud.get_product(product_id)
        if not product:
            logger.warning(f"Product not found", extra={"product_id": str(product_id)})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
            )

        # Получаем реальное доступное количество
        available = await self.cart_service.get_available_quantity(product.id)
        setattr(product, "available_quantity", available)

        logger.debug(
            "Retrieved product details with availability",
            extra={
                "product_id": str(product.id),
                "total_stock": product.stock,
                "available": available,
            },
        )

        return product

    async def search_products(
        self, search_query: str, skip: int = 0, limit: int = 10
    ) -> Tuple[List[Product], int]:
        """
        Поиск товаров с учетом доступного количества

        Args:
            search_query: Поисковый запрос
            skip: Сколько записей пропустить
            limit: Сколько записей вернуть

        Returns:
            Tuple[List[Product], int]: Список товаров и общее количество
        """
        # Получаем результаты поиска через CRUD
        products, total = await self.product_crud.search_products(
            search_query=search_query, skip=skip, limit=limit
        )

        # Для каждого найденного товара считаем реальное доступное количество
        for product in products:
            available = await self.cart_service.get_available_quantity(product.id)
            setattr(product, "available_quantity", available)

            logger.debug(
                "Calculated product availability for search result",
                extra={
                    "product_id": str(product.id),
                    "search_query": search_query,
                    "total_stock": product.stock,
                    "available": available,
                },
            )

        return products, total
