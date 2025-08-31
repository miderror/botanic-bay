import os
import uuid
from typing import Any, List, Optional

from markupsafe import Markup
from passlib.context import CryptContext
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.orm import joinedload
from starlette.datastructures import UploadFile
from starlette.requests import Request
from wtforms import Field, Form
from wtforms.widgets import FileInput

from app.core.settings import settings
from app.models import (
    Category,
    Order,
    PayoutRequest,
    Product,
    ProductImage,
    PromoCode,
    Referral,
    User,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class BasicAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        try:
            form = await request.form()
            username, password = form.get("username"), form.get("password")
            if not username or not password:
                return False
            is_username_correct = username == settings.ADMIN_USER
            is_password_correct = pwd_context.verify(
                password, settings.ADMIN_PASSWORD_HASH
            )
            if is_username_correct and is_password_correct:
                request.session.update({"token": "admin_token"})
                return True
            return False
        except Exception:
            return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "token" in request.session


authentication_backend = BasicAuth(secret_key=settings.SECRET_KEY)


class MultipleFileInput(FileInput):
    """Кастомный виджет, который рендерит <input type="file" multiple>."""

    def __call__(self, field: Field, **kwargs: Any) -> Markup:
        kwargs.setdefault("type", "file")
        kwargs["multiple"] = "true"
        return super().__call__(field, **kwargs)


class MultipleFileField(Field):
    """Кастомное поле WTForms, использующее виджет MultipleFileInput."""

    widget = MultipleFileInput()

    def _value(self) -> List[UploadFile]:
        return []

    def process_formdata(self, valuelist: List[Any]) -> None:
        self.data = valuelist


class UserAdmin(ModelView, model=User):
    name, name_plural, icon = "Пользователь", "Пользователи", "fa-solid fa-user"
    column_list = [
        User.telegram_id,
        User.full_name,
        User.username,
        User.bonus_balance,
        "discount.current_level",
        User.is_active,
        User.roles,
        User.created_at,
    ]
    column_labels = {
        User.telegram_id: "Telegram ID",
        User.full_name: "Полное имя",
        User.username: "Username",
        User.bonus_balance: "Бонусы",
        "discount.current_level": "Скидка",
        User.is_active: "Активен",
        User.roles: "Роли",
        User.created_at: "Регистрация",
    }
    column_searchable_list = [User.telegram_id, User.full_name, User.username]
    column_editable_list = [User.bonus_balance, User.is_active]
    form_columns = [
        User.full_name,
        User.username,
        User.bonus_balance,
        User.is_active,
        User.roles,
    ]
    form_ajax_refs = {"roles": {"fields": ("name",), "order_by": "name"}}


class ProductImageAdmin(ModelView, model=ProductImage):
    name = "Изображение товара"
    name_plural = "Изображения товаров"
    icon = "fa-solid fa-image"
    exclude_from_menu = True
    form_columns = [ProductImage.image_url, ProductImage.position]
    column_labels = {
        ProductImage.image_url: "Файл",
        ProductImage.position: "Порядок",
    }
    form_widget_args = {"position": {"style": "width: 80px;"}}


class ProductAdmin(ModelView, model=Product):
    name, name_plural, icon = "Товар", "Товары", "fa-solid fa-box"

    # column_inline_models = [ProductImageAdmin]
    list_query_load_options = [joinedload(Product.category)]

    form_columns = [
        Product.name,
        Product.description,
        Product.additional_description,
        Product.category,
        Product.price,
        Product.stock,
        Product.sku,
        Product.is_active,
        Product.image_url,
        Product.background_image_url,
        Product.weight,
        Product.length,
        Product.width,
        Product.height,
    ]

    def image_formatter(model, attribute):
        image_proxy = getattr(model, attribute)
        if image_proxy:
            return Markup(
                f'<img src="{str(image_proxy)}" width="60" height="60" style="object-fit: cover; border-radius: 4px;">'
            )
        return ""

    column_formatters = {"image_url": image_formatter}
    column_list = [
        "image_url",
        Product.name,
        Product.category,
        Product.price,
        Product.stock,
        Product.is_active,
    ]
    column_labels = {
        "image_url": "Фото",
        Product.name: "Название",
        Product.category: "Категория",
        Product.price: "Цена",
        Product.stock: "Остаток",
        Product.is_active: "Активен",
    }
    column_searchable_list = [Product.name, "category.name"]
    column_editable_list = [Product.price, Product.stock, Product.is_active]
    form_ajax_refs = {"category": {"fields": ("name",), "order_by": "name"}}


class CategoryAdmin(ModelView, model=Category):
    name, name_plural, icon = "Категория", "Категории", "fa-solid fa-folder-open"
    column_list = [Category.name, Category.description]
    column_labels = {"name": "Название", "description": "Описание"}
    column_searchable_list = [Category.name]


class OrderAdmin(ModelView, model=Order):
    name, name_plural, icon = "Заказ", "Заказы", "fa-solid fa-shopping-cart"
    can_create = False
    column_list = [
        "id",
        "user",
        "status",
        "payment_status",
        "total",
        "track_number",
        "created_at",
    ]
    column_labels = {
        "id": "Номер",
        "user": "Пользователь",
        "status": "Статус",
        "payment_status": "Оплата",
        "total": "Сумма",
        "track_number": "Трек-номер",
        "created_at": "Дата",
    }
    column_searchable_list = ["id", "user.full_name", "track_number"]
    column_sortable_list = ["created_at", "total"]
    column_editable_list = ["status", "payment_status", "track_number"]
    form_columns = [
        "status",
        "payment_status",
        "track_number",
        "delivery_method",
        "delivery_cost",
    ]


class PromoCodeAdmin(ModelView, model=PromoCode):
    name, name_plural, icon = "Промокод", "Промокоды", "fa-solid fa-tags"
    column_list = [
        "code",
        "discount_percent",
        "is_active",
        "uses_left",
        "max_uses",
        "expires_at",
    ]
    column_labels = {
        "code": "Код",
        "discount_percent": "Скидка, %",
        "is_active": "Активен",
        "uses_left": "Осталось",
        "max_uses": "Всего",
        "expires_at": "Действует до",
    }
    column_editable_list = [
        "discount_percent",
        "is_active",
        "uses_left",
        "max_uses",
        "expires_at",
    ]
    form_columns = [
        "code",
        "discount_percent",
        "is_active",
        "max_uses",
        "uses_left",
        "expires_at",
    ]


class ReferralAdmin(ModelView, model=Referral):
    name, name_plural, icon = "Реферал", "Рефералы", "fa-solid fa-users"
    can_create, can_edit = False, False
    column_list = [
        "user.full_name",
        "referrer.user.full_name",
        "is_registered",
        "created_at",
    ]
    column_labels = {
        "user.full_name": "Пользователь",
        "referrer.user.full_name": "Пригласивший",
        "is_registered": "Зарегистрирован",
        "created_at": "Дата",
    }
    column_searchable_list = ["user.full_name", "referrer.user.full_name"]


class PayoutRequestAdmin(ModelView, model=PayoutRequest):
    name, name_plural, icon = (
        "Заявка на вывод",
        "Заявки на вывод",
        "fa-solid fa-hand-holding-dollar",
    )
    can_create = False
    column_list = [
        "user.full_name",
        "amount",
        "status",
        "payment_details",
        "created_at",
    ]
    column_labels = {
        "user.full_name": "Пользователь",
        "amount": "Сумма",
        "status": "Статус",
        "payment_details": "Реквизиты",
        "created_at": "Дата",
    }
    column_editable_list = ["status"]
    column_sortable_list = ["created_at"]


def init_admin(app, engine):
    admin = Admin(
        app,
        engine,
        authentication_backend=authentication_backend,
        title="Админ-панель Botanic Bay",
    )
    admin.add_view(UserAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(PromoCodeAdmin)
    admin.add_view(ReferralAdmin)
    admin.add_view(PayoutRequestAdmin)
