import os

from passlib.context import CryptContext
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.core.logger import logger
from app.core.settings import settings
from app.models import Order, Product, User

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
            is_password_correct = pwd_context.verify(password, settings.ADMIN_PASSWORD_HASH)
            
            logger.info(f"Auth check: user_ok={is_username_correct}, pass_ok={is_password_correct}")

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
        User.id,
        User.telegram_id,
        User.username,
        User.full_name,
        User.is_active,
        User.roles,
    ]
    column_searchable_list = [User.username, User.full_name]
    column_sortable_list = [User.created_at]
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
    column_list = [Order.id, Order.user, Order.status, Order.total, Order.created_at]
    column_searchable_list = [Order.id]
    column_sortable_list = [Order.created_at, Order.total]
    name = "Заказ"
    name_plural = "Заказы"
    icon = "fa-solid fa-shopping-cart"


def init_admin(app, engine):
    admin = Admin(app, engine, authentication_backend=authentication_backend)

    admin.add_view(UserAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(OrderAdmin)
