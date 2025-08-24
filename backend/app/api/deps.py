from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.logger import logger
from app.core.settings import settings
from app.crud.cart import CartCRUD
from app.crud.category import CategoryCRUD
from app.crud.order import OrderCRUD
from app.crud.payment import PaymentCRUD
from app.crud.payout_request import PayoutRequestCRUD
from app.crud.product import ProductCRUD
from app.crud.referral import ReferralCRUD
from app.crud.referral_bonus import ReferralBonusCRUD
from app.crud.user import UserCRUD
from app.crud.user_address import UserAddressCRUD
from app.crud.user_delivery_point import UserDeliveryPointCRUD
from app.crud.user_discount import UserDiscountCRUD
from app.models.user import User
from app.services.cart.cart_service import CartService
from app.services.category.category_service import CategoryService
from app.services.cdek.api import CDEKApi
from app.services.cdek.cdek_service import CDEKService
from app.services.cdek.client import get_cdek_async_client
from app.services.cdek.geocoder.nominatim import NominatimGeocoderService
from app.services.cdek.geocoder.yandex import YandexGeocoderService
from app.services.export.export_service import ExportService
from app.services.order.discount_service import DiscountService
from app.services.payment.payment_service import PaymentService
from app.services.product.product_service import ProductService
from app.services.profile.profile_service import ProfileService
from app.services.referral.referral_service import ReferralService
from app.services.telegram.bot_manager import TelegramBotManager
from app.services.telegram.export_service import TelegramExportService


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User:
    """
    Получение текущего пользователя из Telegram данных

    Args:
        request: FastAPI Request объект
        session: SQLAlchemy сессия

    Returns:
        User: Объект пользователя

    Raises:
        HTTPException: Если пользователь не авторизован
    """
    # Получаем Telegram WebApp данные из заголовков
    telegram_data = request.headers.get("X-Telegram-Init-Data")

    if not telegram_data:
        logger.warning("No Telegram data in request headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    try:
        # Парсим Telegram ID из данных
        # В реальном приложении здесь должна быть валидация данных от Telegram
        # TODO: Добавить правильную валидацию Telegram данных
        telegram_id = int(request.headers.get("X-Telegram-User-Id", 0))

        if not telegram_id:
            raise ValueError("No Telegram ID")

        # Получаем пользователя из БД
        user_crud = UserCRUD(session)
        user = await user_crud.get_by_telegram_id(telegram_id)

        if not user:
            logger.warning(f"User not found for Telegram ID: {telegram_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        if not user.is_active:
            logger.warning(f"User is not active: {telegram_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User is not active"
            )

        return user

    except ValueError as e:
        logger.error("Invalid Telegram data", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication data",
        )
    except Exception as e:
        logger.error("Error getting current user", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Проверка что текущий пользователь является администратором
    """
    if not current_user.has_role("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is not admin"
        )
    return current_user


async def get_profile_service(
    session: AsyncSession = Depends(get_session),
) -> ProfileService:
    return ProfileService(session)


async def get_cart_service(session: AsyncSession = Depends(get_session)) -> CartService:
    """
    Получение сервиса для работы с корзиной

    Args:
        session: SQLAlchemy сессия

    Returns:
        CartService: Сервис для работы с корзиной
    """
    cart_crud = CartCRUD(session)
    product_crud = ProductCRUD(session)
    return CartService(cart_crud, product_crud)


async def get_product_service(
    session: AsyncSession = Depends(get_session),
) -> ProductService:
    """Получение сервиса для работы с продуктами"""
    product_crud = ProductCRUD(session)
    cart_crud = CartCRUD(session)
    cart_service = CartService(cart_crud, product_crud)
    return ProductService(product_crud, cart_service)


async def get_category_service(
    session: AsyncSession = Depends(get_session),
) -> CategoryService:
    """
    Получение экземпляра сервиса для работы с категориями

    Args:
        session: Сессия базы данных

    Returns:
        CategoryService: Экземпляр сервиса для работы с категориями
    """
    category_crud = CategoryCRUD(session)
    return CategoryService(category_crud)


async def get_order_crud(session: AsyncSession = Depends(get_session)) -> OrderCRUD:
    """
    Получение CRUD для работы с заказами

    Args:
        session: SQLAlchemy сессия

    Returns:
        OrderCRUD: CRUD для работы с заказами
    """
    return OrderCRUD(session)


async def get_payment_crud(session: AsyncSession = Depends(get_session)) -> PaymentCRUD:
    """Зависимость для получения CRUD для работы с платежами"""
    return PaymentCRUD(session)


async def get_referral_service(
    session: AsyncSession = Depends(get_session),
) -> ReferralService:
    referral_crud = ReferralCRUD(session)
    referral_bonus_crud = ReferralBonusCRUD(session)
    order_crud = OrderCRUD(session)
    payout_request_crud = PayoutRequestCRUD(session)

    return ReferralService(
        await get_bot_manager(),
        referral_crud,
        referral_bonus_crud,
        order_crud,
        payout_request_crud,
        session,
    )


async def get_discount_service(
    session: AsyncSession = Depends(get_session),
) -> DiscountService:
    discount_crud = UserDiscountCRUD(session)
    order_crud = OrderCRUD(session)

    return DiscountService(
        session,
        discount_crud,
        order_crud,
    )


async def get_payment_service(
    payment_crud: PaymentCRUD = Depends(get_payment_crud),
    order_crud: OrderCRUD = Depends(get_order_crud),
    discount_service: DiscountService = Depends(get_discount_service),
    session: AsyncSession = Depends(get_session),
) -> PaymentService:
    """Зависимость для получения сервиса работы с платежами"""
    return PaymentService(payment_crud, order_crud, discount_service, session)


async def get_export_service(
    session: AsyncSession = Depends(get_session),
    order_crud: OrderCRUD = Depends(get_order_crud),
) -> ExportService:
    """Зависимость для получения сервиса экспорта"""
    return ExportService(session, order_crud)


async def get_cdek_service(session: AsyncSession = Depends(get_session)) -> CDEKService:
    order_crud = OrderCRUD(session)
    user_address_crud = UserAddressCRUD(session)
    user_delivery_point_crud = UserDeliveryPointCRUD(session)
    cdek_api = CDEKApi(
        client_id=settings.CDEK_CLIENT_ID,
        client_secret=settings.CDEK_CLIENT_SECRET.get_secret_value(),
        client=get_cdek_async_client(),
    )
    geocoder_service = NominatimGeocoderService()
    yandex_geocoder_service = YandexGeocoderService(
        api_key=settings.YANDEX_GEOCODER_API_KEY.get_secret_value(),
    )

    return CDEKService(
        cdek_api=cdek_api,
        geocoder_service=geocoder_service,
        yandex_geocoder_service=yandex_geocoder_service,
        user_address_crud=user_address_crud,
        user_delivery_point_crud=user_delivery_point_crud,
    )


# Добавляем зависимость для получения TelegramBotManager
# Глобальная переменная для хранения единственного экземпляра бот-менеджера
_bot_manager_instance = None


async def get_bot_manager() -> TelegramBotManager:
    """Зависимость для получения TelegramBotManager"""
    global _bot_manager_instance

    # Если экземпляр уже создан, возвращаем его
    if _bot_manager_instance is not None:
        return _bot_manager_instance

    # Иначе создаем новый экземпляр
    _bot_manager_instance = TelegramBotManager()
    await _bot_manager_instance.setup()
    return _bot_manager_instance


# Добавляем зависимость для получения TelegramExportService
async def get_telegram_export_service(
    export_service: ExportService = Depends(get_export_service),
    bot_manager: TelegramBotManager = Depends(get_bot_manager),
) -> TelegramExportService:
    return TelegramExportService(export_service, bot_manager)
