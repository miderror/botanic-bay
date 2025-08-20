# backend/app/api/v1/router.py
from fastapi import APIRouter

from app.api.tags import Tags
from app.api.v1.endpoints import (  # , orders, users,
    admin,
    auth,
    cart,
    cdek,
    debug,
    orders,
    payment,
    products,
    proxy,
    referral,
    user,
)

# Создаем основной роутер для API v1
api_router = APIRouter()

# Подключаем все endpoints с префиксами
api_router.include_router(auth.router, prefix="/auth", tags=[Tags.AUTH])

api_router.include_router(user.router, prefix="/user", tags=[Tags.USERS])

api_router.include_router(admin.router, prefix="/admin", tags=[Tags.ADMIN])

api_router.include_router(products.router, prefix="/products", tags=[Tags.PRODUCTS])

api_router.include_router(cart.router, prefix="/cart", tags=[Tags.CART])

api_router.include_router(orders.router, prefix="/orders", tags=[Tags.ORDERS])

api_router.include_router(payment.router, prefix="/payments", tags=[Tags.PAYMENTS])

api_router.include_router(cdek.router, prefix="/cdek", tags=[Tags.CDEK])

api_router.include_router(referral.router, prefix="/referral", tags=[Tags.REFERRAL])

api_router.include_router(debug.router, prefix="/debug", tags=[Tags.DEBUG])

# Добавляем маршрут для проксирования виджета ЮKассы
api_router.include_router(proxy.router, prefix="/proxy", tags=[Tags.PROXY])
