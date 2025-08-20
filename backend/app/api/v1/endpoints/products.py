# backend/app/api/v1/endpoints/products.py
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_cart_service, get_category_service, get_product_service
from app.core.logger import logger
from app.schemas.product import SCategoryList, SProduct, SProductList
from app.services.cart.cart_service import CartService
from app.services.category.category_service import CategoryService
from app.services.product.product_service import ProductService

router = APIRouter()


@router.get("/categories", response_model=SCategoryList)
async def get_product_categories(
    category_service: CategoryService = Depends(get_category_service),
) -> SCategoryList:
    """
    Получение списка всех категорий товаров для пользователей

    Args:
        category_service: Сервис для работы с категориями

    Returns:
        SCategoryList: Схема со списком имен категорий
    """
    try:
        logger.debug("Processing request to get all categories")
        categories = await category_service.get_all_categories()

        # Логируем успешный ответ
        logger.debug(f"Returning categories: {categories}")

        # Создаем и возвращаем объект схемы
        return SCategoryList(categories=categories)

    except Exception as e:
        # Детальное логирование
        logger.error(f"Failed to get product categories: {str(e)}", exc_info=True)

        # Возвращаем ошибку
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories. Error: {str(e)}",
        )


@router.get("/{product_id}/available-quantity")
async def get_available_quantity(
    product_id: UUID, cart_service: CartService = Depends(get_cart_service)
) -> int:
    """
    Получение доступного количества товара с учетом резерваций
    """
    quantity = await cart_service.get_available_quantity(product_id)
    return quantity


@router.get("/search", response_model=SProductList)
@router.get("search/", response_model=SProductList)
async def search_products(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(10, ge=1, le=100, description="Сколько записей вернуть"),
    product_service: ProductService = Depends(get_product_service),
) -> SProductList:
    """
    Поиск товаров по названию

    Args:
        q: Поисковый запрос
        skip: Пагинация - сколько записей пропустить
        limit: Пагинация - сколько записей вернуть
        product_service: Сервис для работы с товарами

    Returns:
        SProductList: Список найденных товаров с пагинацией
    """
    try:
        products, total = await product_service.search_products(
            search_query=q, skip=skip, limit=limit
        )

        # Преобразуем продукты в словари
        products_list = [product.dict() for product in products]

        return SProductList(
            items=products_list,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit,
        )

    except Exception as e:
        logger.error(
            "Failed to process product search", extra={"search_query": q}, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search products",
        )


@router.get("/", response_model=SProductList)
@router.get("", response_model=SProductList)
async def get_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    product_service: ProductService = Depends(get_product_service),
) -> SProductList:
    """
    Получение списка товаров с пагинацией и фильтрацией

    Args:
        skip: Сколько записей пропустить
        limit: Сколько записей вернуть
        category: Фильтр по категории
        product_service: Сервис для работы с товарами

    Returns:
        SProductList: Список товаров с пагинацией
    """
    try:
        # Используем сервис вместо прямого обращения к CRUD
        products, total_count = await product_service.get_products(
            skip=skip, limit=limit, category=category
        )

        # Преобразуем объекты Product в словари
        products_list = [product.dict() for product in products]

        return SProductList(
            items=products_list,
            total=total_count,
            page=skip // limit + 1,
            size=limit,
            pages=(total_count + limit - 1) // limit,
        )

    except Exception as e:
        logger.error("Failed to get products list", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get products",
        )


@router.get("/{product_id}", response_model=SProduct)
@router.get("/{product_id}/", response_model=SProduct)
async def get_product_details(
    product_id: UUID, product_service: ProductService = Depends(get_product_service)
) -> SProduct:
    """
    Получение детальной информации о товаре

    Args:
        product_id: ID товара
        product_service: Сервис для работы с товарами

    Returns:
        SProduct: Детальная информация о товаре

    Raises:
        HTTPException: Если товар не найден
    """
    try:
        logger.info("Getting product details", extra={"product_id": str(product_id)})

        product = await product_service.get_product_details(product_id)

        # Преобразуем в словарь с правильной обработкой изображений
        product_data = product_service.product_crud.to_dict(product)

        logger.info(
            "Product details retrieved successfully",
            extra={"product_id": str(product_id), "product_name": product.name},
        )

        return SProduct(**product_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get product details", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get product details",
        )
