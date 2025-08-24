import os

from passlib.context import CryptContext
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.core.logger import logger
from app.core.settings import settings
from app.models import (
    Order,
    PayoutRequest,
    Product,
    PromoCode,
    Referral,
    ReferralBonus,
    User,
    UserDiscount,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class BasicAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        try:
            logger.info("Attempting to process login form...")
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
            logger.info(f"Form data received: username='{username}'")

            if not username or not password:
                logger.warning("Username or password not provided in form.")
                return False

            is_username_correct = username == settings.ADMIN_USER
            is_password_correct = pwd_context.verify(
                password, settings.ADMIN_PASSWORD_HASH
            )

            logger.info(
                f"Auth check: user_ok={is_username_correct}, pass_ok={is_password_correct}"
            )

            if is_username_correct and is_password_correct:
                logger.info("Login successful, updating session.")
                request.session.update({"token": "admin_token"})
                return True

            logger.warning("Login failed: invalid credentials.")
            return False

        except Exception as e:
            logger.error(f"Error during login process: {e}", exc_info=True)
            return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "token" in request.session


authentication_backend = BasicAuth(secret_key=settings.SECRET_KEY)


class UserAdmin(ModelView, model=User):
    column_list = [
        User.telegram_id,
        User.username,
        User.full_name,
        User.bonus_balance,
        "discount.current_level",
        User.is_active,
        User.roles,
    ]
    column_searchable_list = [User.username, User.full_name, User.telegram_id]
    column_sortable_list = [User.created_at, User.bonus_balance]
    column_editable_list = [User.bonus_balance, User.is_active]
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"


class ProductAdmin(ModelView, model=Product):
    column_list = [
        Product.id,
        Product.name,
        Product.category,
        Product.price,
        Product.stock,
        Product.is_active,
    ]
    column_searchable_list = [Product.name, Product.description]
    column_sortable_list = [Product.price, Product.stock, Product.created_at]
    column_editable_list = [
        Product.price,
        Product.stock,
        Product.is_active,
    ]
    name = "Товар"
    name_plural = "Товары"
    icon = "fa-solid fa-box"


class OrderAdmin(ModelView, model=Order):
    column_list = [
        Order.id,
        Order.user,
        Order.status,
        Order.payment_status,
        Order.total,
        Order.track_number,
        Order.created_at,
    ]
    column_searchable_list = [Order.id, Order.track_number, "user.full_name"]
    column_sortable_list = [Order.created_at, Order.total]
    column_editable_list = [Order.status, Order.track_number, Order.payment_status]
    name = "Заказ"
    name_plural = "Заказы"
    icon = "fa-solid fa-shopping-cart"


class PromoCodeAdmin(ModelView, model=PromoCode):
    column_list = [
        PromoCode.code,
        PromoCode.discount_percent,
        PromoCode.is_active,
        PromoCode.uses_left,
        PromoCode.max_uses,
        PromoCode.expires_at,
    ]
    column_searchable_list = [PromoCode.code]
    column_sortable_list = [PromoCode.created_at, PromoCode.expires_at]
    column_editable_list = [
        PromoCode.discount_percent,
        PromoCode.is_active,
        PromoCode.uses_left,
        PromoCode.max_uses,
    ]
    form_columns = [
        PromoCode.code,
        PromoCode.discount_percent,
        PromoCode.is_active,
        PromoCode.max_uses,
        "uses_left",
        PromoCode.expires_at,
    ]
    name = "Промокод"
    name_plural = "Промокоды"
    icon = "fa-solid fa-tags"


class ReferralAdmin(ModelView, model=Referral):
    name = "Реферал"
    name_plural = "Рефералы"
    icon = "fa-solid fa-users"
    column_list = [
        "user.full_name",
        "referrer.user.full_name",
        Referral.is_registered,
    ]
    column_labels = {
        "user.full_name": "Пользователь",
        "referrer.user.full_name": "Пригласил",
        "is_registered": "Зарегистрирован в реф. системе",
    }
    column_searchable_list = ["user.full_name", "referrer.user.full_name"]


class ReferralBonusAdmin(ModelView, model=ReferralBonus):
    name = "Реферальный бонус"
    name_plural = "Реферальные бонусы"
    icon = "fa-solid fa-money-bill-wave"
    column_list = [
        "referrer.user.full_name",
        "referral.user.full_name",
        ReferralBonus.bonus_amount,
        ReferralBonus.created_at,
    ]
    column_labels = {
        "referrer.user.full_name": "Получатель бонуса",
        "referral.user.full_name": "Приглашенный",
        "bonus_amount": "Сумма бонуса",
        "created_at": "Дата начисления",
    }
    column_sortable_list = [ReferralBonus.created_at, ReferralBonus.bonus_amount]


class PayoutRequestAdmin(ModelView, model=PayoutRequest):
    name = "Заявка на вывод"
    name_plural = "Заявки на вывод"
    icon = "fa-solid fa-hand-holding-dollar"
    column_list = [
        "user.full_name",
        PayoutRequest.amount,
        PayoutRequest.status,
        PayoutRequest.payment_details,
        PayoutRequest.created_at,
    ]
    column_labels = {
        "user.full_name": "Пользователь",
        "amount": "Сумма",
        "status": "Статус",
        "payment_details": "Реквизиты",
        "created_at": "Дата заявки",
    }
    column_editable_list = [PayoutRequest.status]
    column_sortable_list = [PayoutRequest.created_at]


class UserDiscountAdmin(ModelView, model=UserDiscount):
    name = "Скидка пользователя"
    name_plural = "Скидки пользователей"
    icon = "fa-solid fa-percent"
    column_list = [
        "user.full_name",
        UserDiscount.current_level,
        UserDiscount.last_purchase_date,
    ]
    column_labels = {
        "user.full_name": "Пользователь",
        "current_level": "Уровень скидки",
        "last_purchase_date": "Дата последней покупки",
    }
    column_editable_list = [UserDiscount.current_level]
    column_sortable_list = [UserDiscount.last_purchase_date]


def init_admin(app, engine):
    admin = Admin(app, engine, authentication_backend=authentication_backend)

    admin.add_view(UserAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(PromoCodeAdmin)
    admin.add_view(ReferralAdmin)
    admin.add_view(ReferralBonusAdmin)
    admin.add_view(PayoutRequestAdmin)
    admin.add_view(UserDiscountAdmin)
