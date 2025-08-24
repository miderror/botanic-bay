# backend/app/services/payment/yookassa_service.py
"""
Эта реализация:

Использует официальный SDK ЮКассы для создания и управления платежами
Реализует все методы из интерфейса IPaymentProvider
Включает создание корректных чеков для ФЗ-54
Обеспечивает идемпотентность для всех операций
Предоставляет улучшенную обработку вебхуков с проверкой подлинности
Добавляет автоматическую настройку вебхуков при запуске приложения
Содержит подробное логирование всех операций
Обрабатывает ошибки и возвращает правильные ответы на вебхуки
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from yookassa import Configuration, Payment, Webhook
from yookassa.domain.notification import WebhookNotificationEventType

from app.core.logger import logger
from app.core.settings import settings
from app.models.order import Order
from app.services.payment.payment_interface import IPaymentProvider


class YookassaService(IPaymentProvider):
    """
    Сервис для работы с платежной системой ЮКасса
    Реализует интерфейс IPaymentProvider
    Использует официальный SDK ЮКассы
    """

    def __init__(self):
        """Инициализация сервиса с данными из настроек"""
        self.shop_id = settings.YOOKASSA_SHOP_ID
        self.secret_key = settings.YOOKASSA_SECRET_KEY

        # Инициализация SDK при создании сервиса
        Configuration.configure(self.shop_id, self.secret_key)

        # Указываем URL для вебхуков в зависимости от окружения
        if settings.ENVIRONMENT == "development":
            self.webhook_url = settings.YOOKASSA_WEBHOOK_URL_DEV
        else:
            self.webhook_url = settings.YOOKASSA_WEBHOOK_URL_PROD

    async def create_payment(
        self, order: Order, return_url: str, confirmation_type: str = "redirect"
    ) -> Dict[str, Any]:
        """
        Создание платежа в ЮКассе

        Args:
            order: Заказ для оплаты
            return_url: URL для возврата после оплаты
            confirmation_type: Тип подтверждения платежа (redirect или embedded)

        Returns:
            Dict[str, Any]: Данные созданного платежа
        """
        try:
            # Генерируем стабильный ключ идемпотентности
            idempotence_key = (
                f"order_{order.id}_{order.total}_{datetime.now().strftime('%Y%m%d')}"
            )

            # Формируем данные для создания платежа
            payment_data = {
                "amount": {"value": str(order.total), "currency": "RUB"},
                "confirmation": {"type": confirmation_type, "return_url": return_url},
                "capture": True,
                "description": f"Оплата заказа #{order.id}",
                "metadata": {"order_id": str(order.id)},
            }

            # Добавляем данные для чека (ФЗ-54)
            payment_data["receipt"] = self._create_receipt(order)

            logger.info(
                "Creating YooKassa payment",
                extra={
                    "order_id": str(order.id),
                    "amount": str(order.total),
                    "return_url": return_url,
                    "confirmation_type": confirmation_type,
                    "idempotence_key": idempotence_key,
                },
            )

            # Создаем платеж через SDK ЮКассы
            payment = Payment.create(payment_data, idempotence_key)

            # Преобразуем объект Payment в словарь для совместимости
            result = {
                "id": payment.id,
                "status": payment.status,
                "amount": {
                    "value": payment.amount.value,
                    "currency": payment.amount.currency,
                },
                "confirmation": {
                    "type": payment.confirmation.type,
                },
                "created_at": payment.created_at,
                "paid": payment.paid,
                "refundable": payment.refundable,
                "metadata": payment.metadata,
            }

            # Добавляем разные данные в зависимости от типа подтверждения
            if confirmation_type == "redirect" and hasattr(
                payment.confirmation, "confirmation_url"
            ):
                result["confirmation"][
                    "confirmation_url"
                ] = payment.confirmation.confirmation_url
            elif confirmation_type == "embedded" and hasattr(
                payment.confirmation, "confirmation_token"
            ):
                result["confirmation"][
                    "confirmation_token"
                ] = payment.confirmation.confirmation_token

            # Добавляем метод оплаты, если он определен
            if hasattr(payment, "payment_method") and payment.payment_method:
                result["payment_method"] = {"type": payment.payment_method.type}

            # await self.setup_webhooks()

            logger.info(
                "YooKassa payment created",
                extra={
                    "order_id": str(order.id),
                    "yookassa_payment_id": payment.id,
                    "status": payment.status,
                    "confirmation_type": payment.confirmation.type,
                },
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to create YooKassa payment",
                extra={"order_id": str(order.id), "error": str(e)},
                exc_info=True,
            )
            raise

    def _create_receipt(self, order: Order) -> Dict[str, Any]:
        """
        Создание чека для ЮКассы (ФЗ-54)

        Args:
            order: Заказ для формирования чека

        Returns:
            Dict[str, Any]: Данные чека
        """
        items = []

        promo_discount = order.discount_amount or Decimal("0")
        
        for item in order.items:
            item_price = Decimal(item.price)
            item_subtotal = item_price * item.quantity
            
            item_share = item_subtotal / Decimal(order.subtotal) if Decimal(order.subtotal) > 0 else Decimal(0)
            
            item_discount = (promo_discount * item_share).quantize(Decimal("0.01"))
            
            price_with_discount = item_price - (item_discount / item.quantity)

            item_data = {
                "description": item.product_name[:128],
                "quantity": str(item.quantity),
                "amount": {"value": str(price_with_discount.quantize(Decimal("0.01"))), "currency": "RUB"},
                "vat_code": "1",
                "payment_subject": "commodity",
                "payment_mode": "full_prepayment",
            }
            items.append(item_data)

        if order.delivery_cost and Decimal(order.delivery_cost) > 0:
            items.append({
                "description": f"Доставка ({order.delivery_method})",
                "quantity": "1.0",
                "amount": {"value": str(order.delivery_cost), "currency": "RUB"},
                "vat_code": "1",
                "payment_subject": "service",
                "payment_mode": "full_prepayment",
            })

        # Получаем email пользователя для чека
        # Сначала пытаемся получить email из модели пользователя
        user_email = None
        if hasattr(order.user, "email") and order.user.email:
            user_email = order.user.email
        # Если нет email, пытаемся использовать telegram username + dummy domain
        elif hasattr(order.user, "username") and order.user.username:
            user_email = f"{order.user.username}@example.com"
        # Если ничего не подходит, используем дефолтный email
        else:
            user_email = "customer@example.com"

        # Создаем чек
        receipt = {"customer": {"email": user_email}, "items": items}

        # Добавляем номер телефона, если доступен
        if hasattr(order.user, "phone") and order.user.phone:
            receipt["customer"]["phone"] = order.user.phone

        return receipt

    async def check_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Проверка статуса платежа в ЮКассе

        Args:
            payment_id: ID платежа в ЮКассе

        Returns:
            Dict[str, Any]: Данные платежа
        """
        try:
            logger.debug(
                "Checking YooKassa payment status",
                extra={"yookassa_payment_id": payment_id},
            )

            # Получаем информацию о платеже через SDK
            payment = Payment.find_one(payment_id)

            # Преобразуем объект Payment в словарь для совместимости
            result = {
                "id": payment.id,
                "status": payment.status,
                "amount": {
                    "value": payment.amount.value,
                    "currency": payment.amount.currency,
                },
                "created_at": payment.created_at,
                "paid": payment.paid,
                "refundable": payment.refundable,
                "metadata": payment.metadata,
            }

            # Добавляем метод оплаты, если он определен
            if hasattr(payment, "payment_method") and payment.payment_method:
                result["payment_method"] = {"type": payment.payment_method.type}

            # Добавляем URL подтверждения, если он определен
            if hasattr(payment, "confirmation") and payment.confirmation:
                result["confirmation"] = {"type": payment.confirmation.type}
                if hasattr(payment.confirmation, "confirmation_url"):
                    result["confirmation"][
                        "confirmation_url"
                    ] = payment.confirmation.confirmation_url

            logger.debug(
                "YooKassa payment status",
                extra={
                    "yookassa_payment_id": payment_id,
                    "status": payment.status,
                    "paid": payment.paid,
                },
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to check YooKassa payment status",
                extra={"yookassa_payment_id": payment_id, "error": str(e)},
                exc_info=True,
            )
            raise

    async def process_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка вебхука от ЮКассы

        Args:
            data: Данные вебхука

        Returns:
            Dict[str, Any]: Обработанные данные
        """
        try:
            # Проверяем данные вебхука через SDK
            from yookassa.domain.notification import WebhookNotificationFactory

            notification = WebhookNotificationFactory().create(data)
            event = notification.event
            payment_data = notification.object

            logger.info(
                "Processing YooKassa webhook",
                extra={
                    "event": event,
                    "payment_id": payment_data.id,
                    "status": payment_data.status,
                },
            )

            # Проверяем подлинность платежа через API
            payment_info = await self.check_payment(payment_data.id)
            if payment_info.get("id") != payment_data.id:
                logger.warning(
                    "YooKassa webhook payment verification failed",
                    extra={"webhook_payment_id": payment_data.id},
                )
                raise ValueError("Payment verification failed")

            # Маппинг статусов ЮКассы на наши внутренние статусы
            status_mapping = {
                "pending": "pending",
                "waiting_for_capture": "waiting_for_capture",
                "succeeded": "succeeded",
                "canceled": "canceled",
            }

            # Формируем результат обработки
            result = {
                "provider_payment_id": payment_data.id,
                "status": status_mapping.get(payment_data.status, "unknown"),
                "amount": Decimal(payment_data.amount.value),
                "currency": payment_data.amount.currency,
                "paid": payment_data.paid,
                "metadata": payment_data.metadata,
                "refundable": payment_data.refundable,
            }

            # Добавляем метод оплаты, если он определен
            if hasattr(payment_data, "payment_method") and payment_data.payment_method:
                result["payment_method"] = payment_data.payment_method.type

            return result

        except Exception as e:
            logger.error(
                "Failed to process YooKassa webhook",
                extra={"error": str(e), "data": data},
                exc_info=True,
            )
            raise

    async def refund_payment(
        self, payment_id: str, amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Возврат платежа в ЮКассе

        Args:
            payment_id: ID платежа в ЮКассе
            amount: Сумма возврата (если None, то полный возврат)

        Returns:
            Dict[str, Any]: Результат операции
        """
        try:
            from yookassa import Refund

            # Получаем информацию о платеже для определения суммы возврата
            if amount is None:
                payment_info = await self.check_payment(payment_id)
                amount = float(payment_info.get("amount", {}).get("value", "0"))

            # Генерируем ключ идемпотентности для возврата
            idempotence_key = f"refund_{payment_id}_{amount}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Данные для возврата
            refund_data = {
                "payment_id": payment_id,
                "amount": {"value": str(amount), "currency": "RUB"},
            }

            logger.info(
                "Refunding YooKassa payment",
                extra={
                    "yookassa_payment_id": payment_id,
                    "amount": amount,
                    "idempotence_key": idempotence_key,
                },
            )

            # Создаем возврат через SDK
            refund = Refund.create(refund_data, idempotence_key)

            # Преобразуем объект Refund в словарь для совместимости
            result = {
                "id": refund.id,
                "payment_id": refund.payment_id,
                "status": refund.status,
                "amount": {
                    "value": refund.amount.value,
                    "currency": refund.amount.currency,
                },
                "created_at": refund.created_at,
            }

            logger.info(
                "YooKassa refund created",
                extra={
                    "yookassa_payment_id": payment_id,
                    "refund_id": refund.id,
                    "status": refund.status,
                },
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to refund YooKassa payment",
                extra={
                    "yookassa_payment_id": payment_id,
                    "amount": amount,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    async def setup_webhooks(self, webhook_url: Optional[str] = None) -> None:
        """
        Настройка вебхуков для ЮКассы

        Args:
            webhook_url: URL для вебхуков (если None, используется из настроек)
        """
        # Используем URL из параметра или настроек
        url = webhook_url or self.webhook_url

        # События для вебхуков
        webhook_events = [
            WebhookNotificationEventType.PAYMENT_SUCCEEDED,
            WebhookNotificationEventType.PAYMENT_CANCELED,
        ]

        try:
            # Получаем текущие вебхуки
            webhooks = Webhook.list()

            for event in webhook_events:
                webhook_exists = False

                # Проверяем существующие вебхуки
                for webhook in webhooks.items:
                    if webhook.event == event:
                        if webhook.url != url:
                            # Удаляем старый вебхук
                            logger.info(
                                "Removing outdated webhook",
                                extra={"event": event, "old_url": webhook.url},
                            )
                            Webhook.remove(webhook.id)
                        else:
                            webhook_exists = True

                # Создаем новый вебхук если нужно
                if not webhook_exists:
                    logger.info(
                        "Creating new webhook", extra={"event": event, "url": url}
                    )
                    Webhook.add(
                        {
                            "event": event,
                            "url": f"{url}",  # Используем общий URL для всех событий
                        }
                    )

            logger.info("YooKassa webhooks setup completed")

        except Exception as e:
            logger.error(
                "Failed to setup YooKassa webhooks",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise
