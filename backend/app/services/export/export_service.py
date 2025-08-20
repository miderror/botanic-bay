# app/services/export/export_service.py
from datetime import datetime
from typing import Any, BinaryIO, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.crud.order import OrderCRUD
from app.schemas.export import ExportFormat
from app.schemas.order import SOrderFilter
from app.utils.export_utils import generate_csv, generate_excel


class ExportService:
    """Сервис для экспорта данных"""

    def __init__(self, session: AsyncSession, order_crud: OrderCRUD):
        self.session = session
        self.order_crud = order_crud

    async def export_orders(
        self, export_format: ExportFormat, filters: Optional[SOrderFilter] = None
    ) -> Tuple[BinaryIO, str, str]:
        """
        Экспорт заказов в выбранный формат

        Args:
            export_format: Формат экспорта (CSV/Excel)
            filters: Фильтры для выборки заказов

        Returns:
            Tuple[BinaryIO, str, str]: Буфер с данными, имя файла, MIME-тип
        """
        try:
            # Преобразуем фильтры в словарь
            filter_dict = filters.dict(exclude_none=True) if filters else None

            # Получаем заказы с применением фильтров
            orders, total = await self.order_crud.get_orders_for_admin(
                skip=0,  # При экспорте не ограничиваем количество
                limit=10000,  # Ставим большой лимит для экспорта
                filters=filter_dict,
            )

            logger.info(
                "Preparing orders data for export",
                extra={
                    "format": export_format,
                    "orders_count": len(orders),
                    "filters": filter_dict,
                },
            )

            # Преобразуем данные заказов в формат для экспорта
            export_data = self._prepare_orders_export_data(orders)

            # Определяем заголовки для экспорта
            headers = self._get_order_export_headers()

            # Текущая дата для имени файла
            current_date = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Генерируем файл в зависимости от формата
            if export_format == ExportFormat.CSV:
                output = generate_csv(export_data, headers)
                filename = f"orders_export_{current_date}.csv"
                mimetype = "text/csv"
                return output, filename, mimetype

            elif export_format == ExportFormat.EXCEL:
                output = generate_excel(export_data, headers)
                filename = f"orders_export_{current_date}.xlsx"
                mimetype = (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                return output, filename, mimetype

            else:
                raise ValueError(f"Unsupported export format: {export_format}")

        except Exception as e:
            logger.error(
                "Failed to export orders", extra={"error": str(e)}, exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to export orders",
            )

    def _prepare_orders_export_data(self, orders: List) -> List[Dict[str, Any]]:
        """
        Подготовка данных заказов для экспорта

        Args:
            orders: Список заказов

        Returns:
            List[Dict[str, Any]]: Данные для экспорта
        """
        export_data = []

        for order in orders:
            # Базовая информация о заказе
            order_data = {
                "id": str(order.id),
                "status": order.status,
                "created_at": order.created_at.isoformat(),
                "delivery_method": order.delivery_method,
                "delivery_address": order.delivery_address,
                "payment_method": order.payment_method or "",
                "payment_status": order.payment_status or "",
                "subtotal": float(order.subtotal),
                "delivery_cost": float(order.delivery_cost),
                "total": float(order.total),
                "user_id": str(order.user.id) if order.user else "",
                "user_name": order.user.full_name if order.user else "",
                "user_telegram": order.user.username if order.user else "",
                "items_count": len(order.items),
                "items_details": ", ".join(
                    [f"{item.product_name} (x{item.quantity})" for item in order.items]
                ),
            }

            export_data.append(order_data)

        return export_data

    def _get_order_export_headers(self) -> Dict[str, str]:
        """
        Получение заголовков для экспорта заказов

        Returns:
            Dict[str, str]: Словарь маппинга ключей в заголовки
        """
        return {
            "id": "ID заказа",
            "status": "Статус",
            "created_at": "Дата создания",
            "delivery_method": "Способ доставки",
            "delivery_address": "Адрес доставки",
            "payment_method": "Способ оплаты",
            "payment_status": "Статус оплаты",
            "subtotal": "Стоимость товаров",
            "delivery_cost": "Стоимость доставки",
            "total": "Итого",
            "user_id": "ID пользователя",
            "user_name": "Имя пользователя",
            "user_telegram": "Telegram",
            "items_count": "Количество товаров",
            "items_details": "Товары",
        }
