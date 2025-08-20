# backend/app/crud/admin.py
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import String, cast, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.logger import logger
from app.models.category import Category
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import Role, User


class AdminCRUD:
    """
    CRUD операции для админского интерфейса
    Реализует паттерн репозитория для работы с БД
    """

    def __init__(self, session: AsyncSession):
        """
        Инициализация CRUD операций

        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session

    async def get_products_with_stats(
        self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict], int]:
        """
        Получение списка товаров с дополнительной статистикой для админки

        Args:
            skip: Сколько записей пропустить
            limit: Сколько записей вернуть
            filters: Словарь с фильтрами

        Returns:
            Tuple[List[Dict], int]: Список товаров в виде словарей и общее количество
        """
        # Базовый запрос для товаров
        query = select(Product)

        # Применяем фильтры если они есть
        if filters:
            query = self._apply_product_filters(query, filters)

        # Получаем общее количество записей для пагинации
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        # Применяем пагинацию с детерминированной сортировкой
        query = query.order_by(
            Product.created_at.desc(),
            Product.id.desc(),  # Добавляем вторичную сортировку по id
        )
        query = query.offset(skip).limit(limit)

        # Выполняем запрос
        result = await self.session.execute(query)
        products = result.scalars().all()

        # Преобразуем продукты в словари с правильной обработкой категории
        products_data = []
        for product in products:
            product_dict = {
                "id": str(product.id),
                "name": product.name,
                "description": product.description,
                "additional_description": product.additional_description,  # Добавляем новое поле
                "price": float(product.price),
                "stock": product.stock,
                "is_active": product.is_active,
                "category": (
                    product.category.name if product.category else None
                ),  # Берем имя категории
                "image_url": product.image_url,
                "background_image_url": product.background_image_url,
                "additional_images_urls": product.additional_images_urls
                or [],  # Добавляем это поле!
                "sku": product.sku,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
                "total_orders": 0,  # TODO: добавить реальную статистику
                "last_ordered_at": None,  # TODO: добавить реальную статистику
            }
            products_data.append(product_dict)

        logger.debug(
            "Retrieved products for admin",
            extra={"total": total, "skip": skip, "limit": limit, "filters": filters},
        )

        return products_data, total

    def _apply_product_filters(self, query, filters: Dict[str, Any]):
        """
        Применяет фильтры к запросу товаров

        Args:
            query: Базовый SQLAlchemy запрос
            filters: Словарь с фильтрами

        Returns:
            Query: Запрос с примененными фильтрами
        """
        if name := filters.get("name"):
            query = query.where(Product.name.ilike(f"%{name}%"))

        if category := filters.get("category"):
            query = query.join(Category).where(Category.name == category)

        # Изменяем логику фильтра is_active
        if is_active := filters.get("is_active"):
            # Применяем фильтр только если значение True
            # Если False - не применяем фильтр вообще
            query = query.where(Product.is_active == True)

        return query

    async def get_users_with_roles(
        self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Получение списка пользователей с их ролями для админки

        Args:
            skip: Сколько записей пропустить
            limit: Сколько записей вернуть
            filters: Словарь с фильтрами

        Returns:
            Tuple[List[Dict[str, Any]], int]: Список пользователей с ролями и общее количество
        """
        # Базовый запрос с подгрузкой ролей
        query = select(User).options(joinedload(User.roles))

        if filters:
            query = self._apply_user_filters(query, filters)

        # Получаем общее количество записей
        total = await self.session.scalar(
            select(func.count()).select_from(query.subquery())
        )

        # Добавляем пагинацию и детерминированную сортировку
        query = query.order_by(
            User.created_at.desc(),
            User.id.desc(),  # Добавляем вторичную сортировку по id
        )
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)

        # Используем unique() для предотвращения дубликатов при eager loading
        users = result.unique().scalars().all()

        # Преобразуем пользователей в словари с правильно преобразованными ролями
        user_dicts = []
        for user in users:
            user_dict = {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "full_name": user.full_name,
                "referral_code": user.referral_code,
                "is_active": user.is_active,
                "roles": user.role_names,  # Используем новый метод
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                # Добавляем остальные поля для админского интерфейса
                "total_orders": 0,  # TODO: Добавить реальные данные
                "total_spent": 0.0,  # TODO: Добавить реальные данные
                "last_order_at": None,  # TODO: Добавить реальные данные
            }
            user_dicts.append(user_dict)

        return user_dicts, total

    def _apply_user_filters(self, query, filters: Dict[str, Any]):
        """
        Применяет фильтры к запросу пользователей

        Args:
            query: Базовый SQLAlchemy запрос
            filters: Словарь с фильтрами

        Returns:
            Query: Запрос с примененными фильтрами
        """
        if username := filters.get("username"):
            query = query.where(User.username.ilike(f"%{username}%"))

        if telegram_id := filters.get("telegram_id"):
            # Преобразуем telegram_id в строку и ищем вхождение
            query = query.where(
                cast(User.telegram_id, String).ilike(f"%{telegram_id}%")
            )

        if role := filters.get("role"):
            query = query.join(User.roles).where(Role.name == role)

        if is_active := filters.get("is_active"):
            query = query.where(User.is_active == True)

        return query

    async def toggle_user_block(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Переключение статуса блокировки пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Optional[Dict[str, Any]]: Данные пользователя в виде словаря или None если не найден
        """
        try:
            # Получаем пользователя с предзагрузкой ролей
            query = (
                select(User).options(joinedload(User.roles)).where(User.id == user_id)
            )
            result = await self.session.execute(query)
            user = result.unique().scalar_one_or_none()

            if not user:
                return None

            # Инвертируем статус активности
            user.is_active = not user.is_active
            await self.session.commit()

            # Обновляем пользователя для получения актуального updated_at
            await self.session.refresh(user)

            # Формируем ответ в нужном формате
            response_data = {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "full_name": user.full_name,
                "referral_code": user.referral_code,
                "is_active": user.is_active,
                "roles": [
                    role.name for role in user.roles
                ],  # Преобразуем роли в строки
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "total_orders": 0,  # TODO: Добавить реальные данные
                "total_spent": 0.0,  # TODO: Добавить реальные данные
                "last_order_at": None,  # TODO: Добавить реальные данные
            }

            logger.info(
                "Toggled user block status",
                extra={"user_id": str(user_id), "is_active": user.is_active},
            )

            return response_data

        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to toggle user block status", exc_info=True)
            raise

    # В методе get_product_categories заменим старую реализацию:
    async def get_product_categories(self) -> list[str]:
        """
        Получение списка всех уникальных категорий товаров

        Returns:
            list[str]: Список названий категорий
        """
        query = select(Category)
        result = await self.session.execute(query)
        categories = result.scalars().all()

        # Возвращаем только названия для сохранения совместимости
        category_names = [cat.name for cat in categories if cat.name]

        logger.debug(f"Retrieved {len(category_names)} product categories")
        return sorted(category_names)

    async def update_user_roles(
        self, user_id: UUID, role_names: List[str]
    ) -> Optional[User]:
        """
        Обновление ролей пользователя

        Args:
            user_id: ID пользователя
            role_names: Список названий ролей

        Returns:
            Optional[User]: Обновленный пользователь или None если не найден
        """
        try:
            # Получаем пользователя
            query = (
                select(User).options(joinedload(User.roles)).where(User.id == user_id)
            )
            result = await self.session.execute(query)
            user = result.unique().scalar_one_or_none()

            if not user:
                logger.warning(f"User not found: {user_id}")
                return None

            # Получаем роли из БД
            roles_query = select(Role).where(Role.name.in_(role_names))
            result = await self.session.execute(roles_query)
            roles = result.scalars().all()

            if len(roles) != len(role_names):
                found_roles = {role.name for role in roles}
                missing_roles = set(role_names) - found_roles
                raise ValueError(f"Roles not found: {missing_roles}")

            # Обновляем роли
            user.roles = roles
            await self.session.commit()
            await self.session.refresh(user)

            logger.info(
                f"Updated roles for user {user_id}",
                extra={"user_id": str(user_id), "new_roles": role_names},
            )

            return user

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating user roles: {str(e)}", exc_info=True)
            raise

    async def get_orders_for_admin(
        self, skip: int = 0, limit: int = 50, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Order], int]:
        """
        Получение списка заказов для админского интерфейса с фильтрацией

        Args:
            skip: Сколько записей пропустить
            limit: Сколько записей вернуть
            filters: Словарь с фильтрами

        Returns:
            Tuple[List[Order], int]: Список заказов и общее количество
        """
        try:
            # Загружаем связанные данные
            query = select(Order).options(
                joinedload(Order.user),
                joinedload(Order.items).joinedload(OrderItem.product),
            )

            # Применяем фильтры
            if filters:
                # Фильтр по ID заказа
                if order_id := filters.get("order_id"):
                    # Используем cast и ilike для поиска по части UUID
                    query = query.where(cast(Order.id, String).ilike(f"%{order_id}%"))

                # Фильтр по статусу
                if status := filters.get("status"):
                    query = query.where(Order.status == status)

                # Фильтр по дате
                if from_date := filters.get("from_date"):
                    query = query.where(Order.created_at >= from_date)
                if to_date := filters.get("to_date"):
                    query = query.where(Order.created_at <= to_date)

                # Фильтр по сумме заказа
                if min_total := filters.get("min_total"):
                    query = query.where(Order.total >= min_total)
                if max_total := filters.get("max_total"):
                    query = query.where(Order.total <= max_total)

            # Получаем общее количество записей
            count_query = select(func.count()).select_from(query.subquery())
            total = await self.session.scalar(count_query)

            # Добавляем сортировку и пагинацию
            query = query.order_by(desc(Order.created_at)).offset(skip).limit(limit)

            # Выполняем запрос
            result = await self.session.execute(query)
            orders = result.unique().scalars().all()

            logger.info(
                "Retrieved orders for admin",
                extra={
                    "total_orders": total,
                    "returned_orders": len(orders),
                    "filters": filters,
                },
            )

            return orders, total or 0

        except Exception as e:
            logger.error(
                "Failed to get orders for admin",
                extra={"error": str(e), "filters": filters},
                exc_info=True,
            )
            raise

    async def update_order_status(
        self, order_id: UUID, status: str, comment: Optional[str] = None
    ) -> Optional[Order]:
        """
        Обновление статуса заказа администратором

        Args:
            order_id: ID заказа
            status: Новый статус
            comment: Комментарий к изменению статуса

        Returns:
            Optional[Order]: Обновленный заказ
        """
        try:
            # Сначала получаем и обновляем сам заказ
            order = await self.session.get(Order, order_id)
            if not order:
                return None

            # Обновляем статус
            order.status = status

            # Добавляем комментарий в историю если есть
            if comment:
                if not hasattr(order, "status_history"):
                    order.status_history = []

                order.status_history.append(
                    {
                        "status": status,
                        "comment": comment,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            await self.session.commit()

            # После обновления загружаем все связанные данные
            query = (
                select(Order)
                .options(
                    joinedload(Order.user),
                    joinedload(Order.items).joinedload(OrderItem.product),
                )
                .where(Order.id == order_id)
            )

            result = await self.session.execute(query)
            updated_order = result.unique().scalar_one_or_none()

            logger.info(
                "Order status updated",
                extra={
                    "order_id": str(order_id),
                    "new_status": status,
                    "comment": comment,
                },
            )

            return updated_order

        except Exception as e:
            logger.error(
                "Failed to update order status",
                extra={
                    "order_id": str(order_id),
                    "new_status": status,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def get_order_stats(self) -> Dict[str, Any]:
        """
        Получение статистики по заказам

        Returns:
            Dict[str, Any]: Статистика заказов
        """
        try:
            # Запрос для общих показателей
            stats_query = select(
                func.count(Order.id).label("total_count"),
                func.sum(Order.total).label("total_revenue"),
                func.avg(Order.total).label("average_order_value"),
            )

            # Выполняем запрос
            result = await self.session.execute(stats_query)
            row = result.first()

            # Запрос для подсчета заказов по статусам
            status_query = select(Order.status, func.count(Order.id)).group_by(
                Order.status
            )

            status_result = await self.session.execute(status_query)
            status_counts = dict(status_result.all())

            stats = {
                "total_count": row.total_count or 0,
                "total_revenue": float(row.total_revenue or 0),
                "average_order_value": float(row.average_order_value or 0),
                "status_counts": status_counts,
            }

            logger.info("Retrieved order statistics", extra={"stats": stats})

            return stats

        except Exception as e:
            logger.error(
                "Failed to get order statistics", extra={"error": str(e)}, exc_info=True
            )
            raise
