# backend/app/api/tags.py
from enum import Enum


class Tags(str, Enum):
    """Теги для группировки эндпоинтов в документации"""

    AUTH = "auth"
    USERS = "users"
    PRODUCTS = "products"
    ORDERS = "orders"
    ADMIN = "admin"
    CART = "cart"
    PAYMENTS = "payments"
    CDEK = "cdek"
    REFERRAL = "referral"
    DEBUG = "debug"
    PROXY = "proxy"

    @classmethod
    def get_all_tags(cls):
        return [
            {"name": cls.AUTH.value, "description": "Authentication endpoints"},
            {"name": cls.USERS.value, "description": "User management"},
            {"name": cls.PRODUCTS.value, "description": "Product operations"},
            {"name": cls.ORDERS.value, "description": "Order management"},
            {"name": cls.ADMIN.value, "description": "Admin operations"},
            {"name": cls.CART.value, "description": "Shopping cart operations"},
            {"name": cls.ORDERS.value, "description": "Order management"},
            {"name": cls.PAYMENTS.value, "description": "Payment operations"},
            {"name": cls.CDEK.value, "description": "CDEK operations"},
            {"name": cls.REFERRAL.value, "description": "REFERRAL operations"},
            {"name": cls.DEBUG.value, "description": "Debug endpoints"},
            {"name": cls.PROXY.value, "description": "Proxy endpoints"},
        ]
