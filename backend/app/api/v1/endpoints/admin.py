# backend/app/api/v1/endpoints/admin.py
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)

# Для экспорта CSV/Excel
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_admin,
    get_export_service,
    get_referral_service,
    get_telegram_export_service,
)
from app.core.db import get_session
from app.core.logger import logger
from app.core.settings import settings
from app.crud.admin import AdminCRUD
from app.crud.product import ProductCRUD
from app.enums.referral import ReferralPayoutStatus
from app.models.user import User
from app.schemas.admin import (
    SAdminOrderList,
    SAdminProductList,
    SAdminProductResponse,
    SAdminUserList,
    SAdminUserResponse,
    SOrder,
    SUpdateOrderStatus,
    SUpdateUserRoles,
)
from app.schemas.export import SExportOrdersRequest
from app.schemas.product import SProduct, SProductCreate, SProductUpdate
from app.schemas.referral import SReferralPayoutRequest, SReferralPayoutRequestPaginated
from app.services.export.export_service import ExportService
from app.services.referral.referral_service import ReferralService
from app.services.telegram.export_service import TelegramExportService
from app.utils.files import save_upload_file

# Добавляем новые импорты

router = APIRouter()


@router.get("/products/categories", response_model=list[str])
async def get_product_categories(
    session: AsyncSession = Depends(get_session), _: User = Depends(get_current_admin)
) -> list[str]:
    """
    Получение списка всех категорий товаров
    """
    try:
        admin_crud = AdminCRUD(session)
        categories = await admin_crud.get_product_categories()
        return categories

    except Exception as e:
        logger.error("Failed to get product categories", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get categories",
        )


# Управление товарами
@router.get("/products", response_model=SAdminProductList)
async def get_products_admin(
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(50, ge=1, le=100, description="Сколько записей вернуть"),
    name: Optional[str] = Query(None, description="Фильтр по названию товара"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    is_active: Optional[bool] = Query(None, description="Фильтр по статусу активности"),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
) -> SAdminProductList:
    """
    Получение списка товаров для админского интерфейса
    """
    try:
        admin_crud = AdminCRUD(session)

        # Собираем фильтры в словарь
        filters = {}
        if name is not None:
            filters["name"] = name
        if category is not None:
            filters["category"] = category
        if is_active is not None:
            filters["is_active"] = is_active

        logger.debug("Applying filters", extra={"filters": filters})

        products, total = await admin_crud.get_products_with_stats(
            skip=skip, limit=limit, filters=filters
        )

        return SAdminProductList(
            items=products,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit,
        )

    except Exception as e:
        logger.error("Failed to get products for admin", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get products",
        )


@router.patch("/products/{product_id}", response_model=SProduct)
async def update_product(
    product_id: UUID,
    product_data: SProductUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
) -> SProduct:
    """
    Частичное обновление товара
    """
    product_crud = ProductCRUD(session)
    updated_product = await product_crud.update_product(product_id, product_data)

    if not updated_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )

    # Преобразуем продукт в словарь, совместимый со схемой SProduct
    return SProduct(**product_crud.to_dict(updated_product))


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
):
    """
    Удаление товара
    """
    product_crud = ProductCRUD(session)
    deleted = await product_crud.delete_product(product_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        )


@router.post("/products", response_model=SAdminProductResponse)
async def create_product(
    product_data: SProductCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
) -> SAdminProductResponse:
    """
    Создание нового товара через админский интерфейс

    Args:
        product_data: Данные нового товара
        session: Сессия БД
        _: Текущий пользователь (должен быть админом)

    Returns:
        SAdminProductResponse: Созданный товар с дополнительными полями для админки
    """
    try:
        # Создаем товар через CRUD
        product_crud = ProductCRUD(session)
        product = await product_crud.create_product(product_data)

        # Правильно преобразуем продукт в словарь для ответа
        response_data = {
            "id": str(product.id),
            "name": product.name,
            "description": product.description,
            "additional_description": product.additional_description,
            "price": float(product.price),
            "stock": product.stock,
            "is_active": product.is_active,
            "category": (
                product.category.name if product.category else None
            ),  # Берем имя категории
            "image_url": product.image_url,
            "background_image_url": product.background_image_url,
            "additional_images_urls": product.additional_images_urls or [],
            "sku": product.sku,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "total_orders": 0,  # Новый товар, заказов еще нет
            "last_ordered_at": None,  # Дата последнего заказа отсутствует
        }

        logger.info(
            "Created new product via admin interface",
            extra={
                "product_id": str(product.id),
                "product_name": product.name,
                "category": response_data["category"],
            },
        )

        return SAdminProductResponse(**response_data)

    except Exception as e:
        logger.error("Failed to create product", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product",
        )


# Управление пользователями


@router.get("/users", response_model=SAdminUserList)
async def get_users_admin(
    skip: int = Query(0, ge=0, description="Сколько записей пропустить"),
    limit: int = Query(50, ge=1, le=100, description="Сколько записей вернуть"),
    username: Optional[str] = Query(None, description="Фильтр по имени пользователя"),
    telegram_id: Optional[int] = Query(None, description="Фильтр по Telegram ID"),
    role: Optional[str] = Query(None, description="Фильтр по роли"),
    is_active: Optional[bool] = Query(None, description="Фильтр по статусу активности"),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
) -> SAdminUserList:
    try:
        admin_crud = AdminCRUD(session)

        # Собираем фильтры в словарь
        filters = {}
        if username is not None:
            filters["username"] = username
        if telegram_id is not None:
            filters["telegram_id"] = telegram_id
        if role is not None:
            filters["role"] = role
        if is_active is not None:
            filters["is_active"] = is_active

        logger.debug("Applying user filters", extra={"filters": filters})

        users, total = await admin_crud.get_users_with_roles(
            skip=skip, limit=limit, filters=filters
        )

        return SAdminUserList(
            items=users,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit,
        )

    except Exception as e:
        logger.error("Failed to get users for admin", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users",
        )


@router.patch("/users/{user_id}/block", response_model=SAdminUserResponse)
async def block_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_admin: User = Depends(get_current_admin),
) -> SAdminUserResponse:
    """
    Блокировка/разблокировка пользователя

    Args:
        user_id: ID пользователя
        session: Сессия БД
        current_admin: Текущий админ

    Returns:
        SAdminUserResponse: Обновленный пользователь

    Raises:
        HTTPException: При ошибке блокировки/разблокировки
    """
    try:
        admin_crud = AdminCRUD(session)

        # Проверяем что админ не пытается заблокировать себя
        if user_id == current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot block yourself"
            )

        user_data = await admin_crud.toggle_user_block(user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return SAdminUserResponse(**user_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to toggle user block status", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle user block status",
        )


@router.patch("/users/{user_id}/roles", response_model=SAdminUserResponse)
async def update_user_roles(
    user_id: UUID,
    roles_data: SUpdateUserRoles,
    session: AsyncSession = Depends(get_session),
    current_admin: User = Depends(get_current_admin),
) -> SAdminUserResponse:
    """
    Обновление ролей пользователя

    Args:
        user_id: ID пользователя
        roles_data: Новые роли пользователя
        session: Сессия БД
        current_admin: Текущий админ

    Returns:
        SAdminUserResponse: Обновленный пользователь

    Raises:
        HTTPException: Если возникла ошибка при обновлении
    """
    try:
        # Проверяем что админ не пытается изменить свои роли
        if user_id == current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify own roles",
            )

        admin_crud = AdminCRUD(session)
        user = await admin_crud.update_user_roles(user_id, roles_data.roles)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Преобразуем в ответ API
        response_data = {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "full_name": user.full_name,
            "referral_code": user.referral_code,
            "is_active": user.is_active,
            "roles": user.role_names,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "total_orders": 0,  # TODO: Добавить реальные данные
            "total_spent": 0.0,  # TODO: Добавить реальные данные
            "last_order_at": None,  # TODO: Добавить реальные данные
        }

        return SAdminUserResponse(**response_data)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user roles", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user roles",
        )


@router.post("/products/upload-image")
async def upload_product_image(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
) -> dict:
    """
    Загрузка изображения товара

    Args:
        file: Загружаемый файл
        session: Сессия БД
        _: Текущий пользователь (должен быть админом)

    Returns:
        dict: Путь к сохраненному файлу

    Raises:
        HTTPException: При ошибках валидации или сохранения
    """
    # Проверяем тип файла
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed types: JPG, PNG, WEBP",
        )

    # Читаем содержимое для проверки размера
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB",
        )

    # Возвращаем файл в начальное положение
    await file.seek(0)

    # Сохраняем файл
    saved_path = await save_upload_file(file, "products")
    if not saved_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image",
        )

    logger.info(
        "Product image uploaded successfully",
        extra={
            "uploaded_file": file.filename,  # Изменили ключ с filename на uploaded_file
            "content_type": file.content_type,
            "size": len(contents),
            "saved_path": saved_path,
        },
    )

    return {"image_url": saved_path}


# ЗАКАЗЫ


# Добавить эндпоинт:
@router.post("/orders/export")
async def export_orders(
    export_data: SExportOrdersRequest,
    export_service: ExportService = Depends(get_export_service),
    _: User = Depends(get_current_admin),
):
    """
    Экспорт заказов в выбранном формате

    Args:
        export_data: Данные для экспорта
        export_service: Сервис экспорта
        _: Текущий пользователь (должен быть админом)

    Returns:
        StreamingResponse: Файл с экспортированными данными
    """
    try:
        # Получаем буфер с данными, имя файла и MIME-тип
        buffer, filename, mimetype = await export_service.export_orders(
            export_format=export_data.format, filters=export_data.filters
        )

        # Возвращаем файл для скачивания
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

        logger.info(
            "Orders export successful",
            extra={
                "format": export_data.format,
                "export_filename": filename,  # Переименовать ключ на export_filename
            },
        )

        return StreamingResponse(buffer, media_type=mimetype, headers=headers)

    except Exception as e:
        logger.error("Failed to export orders", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export orders: {str(e)}",
        )


@router.post("/orders/export-to-telegram")
async def export_orders_to_telegram(
    export_data: SExportOrdersRequest,
    telegram_user_id: int = Query(..., description="Telegram User ID"),
    telegram_export_service: TelegramExportService = Depends(
        get_telegram_export_service
    ),
    _: User = Depends(get_current_admin),
):
    """
    Экспорт заказов и отправка файла через Telegram бота
    """
    try:
        # Добавляем дополнительное логирование, исправлено для работы с Pydantic моделью
        logger.info(
            "Starting orders export via Telegram",
            extra={
                "telegram_user_id": telegram_user_id,
                "export_format": export_data.format.value,
                # Исправлено: проверяем поля модели SOrderFilter, не используя values()
                "filters_applied": export_data.filters is not None,
            },
        )

        # Проверяем валидность telegram_user_id
        if telegram_user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Telegram user ID",
            )

        # Вызываем сервис экспорта
        result = await telegram_export_service.export_orders_to_telegram(
            chat_id=telegram_user_id,
            export_format=export_data.format,
            filters=export_data.filters,
        )

        if result:
            logger.info(
                "Orders export to Telegram successful",
                extra={
                    "telegram_user_id": telegram_user_id,
                    "export_format": export_data.format.value,
                },
            )

            return {"success": True, "message": "Файл успешно отправлен в Telegram"}
        else:
            logger.error(
                "Orders export to Telegram failed",
                extra={
                    "telegram_user_id": telegram_user_id,
                    "export_format": export_data.format.value,
                },
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send file via Telegram bot",
            )

    except Exception as e:
        logger.error(
            f"Failed to export orders to Telegram: {str(e)}",
            extra={
                "telegram_user_id": telegram_user_id,
                "export_format": (
                    export_data.format.value
                    if hasattr(export_data, "format")
                    else "unknown"
                ),
                "error_details": str(e),
            },
            exc_info=True,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export orders to Telegram: {str(e)}",
        )


@router.get("/orders", response_model=SAdminOrderList)
async def get_orders_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    order_id: Optional[str] = Query(None, description="Фильтр по ID заказа"),
    from_date: Optional[datetime] = Query(None, description="Фильтр по дате от"),
    to_date: Optional[datetime] = Query(None, description="Фильтр по дате до"),
    min_total: Optional[float] = Query(None, description="Фильтр по минимальной сумме"),
    max_total: Optional[float] = Query(
        None, description="Фильтр по максимальной сумме"
    ),
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
) -> SAdminOrderList:
    """
    Получение списка заказов для админского интерфейса
    """
    try:
        admin_crud = AdminCRUD(session)

        # Собираем фильтры в словарь
        filters = {}
        if order_id:
            filters["order_id"] = order_id
        if status:
            filters["status"] = status
        if from_date:
            filters["from_date"] = from_date
        if to_date:
            filters["to_date"] = to_date
        if min_total is not None:
            filters["min_total"] = min_total
        if max_total is not None:
            filters["max_total"] = max_total

        logger.debug("Applying order filters", extra={"filters": filters})

        orders, total = await admin_crud.get_orders_for_admin(
            skip=skip, limit=limit, filters=filters
        )

        return SAdminOrderList(
            items=orders,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit,
        )
    except Exception as e:
        logger.error("Failed to get orders for admin", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders",
        )


@router.patch("/orders/{order_id}/status", response_model=SOrder)
async def update_order_status_admin(
    order_id: UUID,
    data: SUpdateOrderStatus,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_admin),
) -> SOrder:
    """
    Обновление статуса заказа администратором

    Args:
        order_id: ID заказа
        data: Новый статус
        session: Сессия БД
        _: Текущий пользователь (должен быть админом)

    Returns:
        SOrder: Обновленный заказ

    Raises:
        HTTPException: При ошибке обновления
    """
    try:
        admin_crud = AdminCRUD(session)

        order = await admin_crud.update_order_status(
            order_id, data.status, data.comment if hasattr(data, "comment") else None
        )

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        logger.info(
            "Order status updated by admin",
            extra={"order_id": str(order_id), "new_status": data.status},
        )

        return order

    except Exception as e:
        logger.error(
            "Failed to update order status",
            extra={"order_id": str(order_id), "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status",
        )


@router.get("/payout-request", response_model=SReferralPayoutRequestPaginated)
async def get_payout_requests(
    request_id: Optional[UUID] = Query(None, alias="id"),
    status_: Optional[ReferralPayoutStatus] = Query(None, alias="status"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(50),
    _: User = Depends(get_current_admin),
    referral_service: ReferralService = Depends(get_referral_service),
):
    try:
        return await referral_service.get_payout_requests(
            request_id=request_id,
            status_=status_,
            from_date=from_date,
            to_date=to_date,
            page=page,
            page_size=page_size,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch payout requests (paginated)",
            extra={"page": str(page), "page_size": page_size, "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payout requests (paginated)",
        )


@router.post(
    "/payout-request/{request_id}/approve", response_model=SReferralPayoutRequest
)
async def approve_payout_request(
    request_id: Annotated[UUID, Path(..., description="ID заявки")],
    referral_service: ReferralService = Depends(get_referral_service),
    _: User = Depends(get_current_admin),
):
    try:
        return await referral_service.approve_payout_request(request_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to approve payout request",
            extra={"request_id": str(request_id), "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve payout request",
        )


@router.post(
    "/payout-request/{request_id}/reject", response_model=SReferralPayoutRequest
)
async def reject_payout_request(
    request_id: Annotated[UUID, Path(..., description="ID заявки")],
    referral_service: ReferralService = Depends(get_referral_service),
    _: User = Depends(get_current_admin),
):
    try:
        return await referral_service.reject_payout_request(request_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to reject payout request",
            extra={"request_id": str(request_id), "detail": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject payout request",
        )
