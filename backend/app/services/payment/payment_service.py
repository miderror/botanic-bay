# backend/app/services/payment/payment_service.py
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.crud.order import OrderCRUD
from app.crud.payment import PaymentCRUD
from app.models.payment import Payment
from app.schemas.payment import (
    PaymentProvider,
    PaymentStatus,
    SPaymentCreate,
    SPaymentUpdate,
)
from app.services.order.discount_service import DiscountService
from app.services.payment.payment_interface import IPaymentProvider
from app.services.payment.yookassa_service import YookassaService


class PaymentService:
    """
    Сервис для работы с платежами
    Обеспечивает единый интерфейс для работы с разными платежными системами
    """

    def __init__(
        self,
        payment_crud: PaymentCRUD,
        order_crud: OrderCRUD,
        discount_service: DiscountService,
        session: AsyncSession,
    ):
        self.payment_crud = payment_crud
        self.order_crud = order_crud
        self.discount_service = discount_service
        self.session = session

        # Словарь с доступными провайдерами платежей
        self.providers: Dict[str, IPaymentProvider] = {
            PaymentProvider.YOOKASSA.value: YookassaService()
        }

    def _get_provider(self, provider_name: str) -> IPaymentProvider:
        """
        Получение провайдера платежей по имени

        Args:
            provider_name: Название провайдера

        Returns:
            IPaymentProvider: Экземпляр провайдера

        Raises:
            ValueError: Если провайдер не найден
        """
        provider = self.providers.get(provider_name.lower())
        if not provider:
            logger.error(f"Unknown payment provider: {provider_name}")
            raise ValueError(f"Unknown payment provider: {provider_name}")
        return provider

    async def create_payment(
        self, order_id: UUID, provider_name: str, return_url: str
    ) -> Tuple[Payment, str]:
        """
        Создание платежа для заказа

        Args:
            order_id: ID заказа
            provider_name: Название провайдера
            return_url: URL возврата после оплаты

        Returns:
            Tuple[Payment, str]: Созданный платеж и URL для оплаты

        Raises:
            HTTPException: При ошибке создания платежа
        """
        # Получаем заказ
        order = await self.order_crud.get_order(order_id)
        if not order:
            logger.warning("Order not found", extra={"order_id": str(order_id)})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        # Проверяем статус заказа
        if order.status not in ["pending", "created"]:
            logger.warning(
                "Invalid order status for payment",
                extra={"order_id": str(order_id), "status": order.status},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order already paid or canceled",
            )

        try:
            # Получаем провайдера
            provider = self._get_provider(provider_name)

            # Создаем платеж в провайдере
            provider_response = await provider.create_payment(order, return_url)

            # Получаем URL для оплаты
            confirmation_url = provider_response.get("confirmation", {}).get(
                "confirmation_url"
            )
            if not confirmation_url:
                logger.error(
                    "No confirmation URL in provider response",
                    extra={
                        "order_id": str(order_id),
                        "provider": provider_name,
                        "response": provider_response,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Payment system error",
                )

            # Создаем платеж в нашей БД
            payment_data = SPaymentCreate(
                order_id=order_id,
                provider=provider_name,
                amount=order.total,
                currency="RUB",
                payment_method=provider_response.get("payment_method", {}).get("type"),
            )

            payment = await self.payment_crud.create_payment(payment_data)

            # Обновляем данные платежа из ответа провайдера
            payment_update = SPaymentUpdate(
                provider_payment_id=provider_response.get("id"),
                status=provider_response.get("status", "pending"),
                confirmation_url=confirmation_url,
                payment_data=provider_response,
            )

            payment = await self.payment_crud.update_payment(payment.id, payment_update)

            # Обновляем статус заказа и метод оплаты
            order.payment_method = provider_name
            order.payment_status = "pending"
            await self.session.commit()

            logger.info(
                "Payment created successfully",
                extra={
                    "payment_id": str(payment.id),
                    "order_id": str(order_id),
                    "provider": provider_name,
                    "confirmation_url": confirmation_url,
                },
            )

            return payment, confirmation_url

        except ValueError as e:
            logger.error("Invalid provider", extra={"error": str(e)}, exc_info=True)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(
                "Failed to create payment",
                extra={
                    "order_id": str(order_id),
                    "provider": provider_name,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment",
            )

    async def check_payment_status(self, payment_id: UUID) -> Payment:
        """
        Проверка статуса платежа

        Args:
            payment_id: ID платежа

        Returns:
            Payment: Обновленный платеж

        Raises:
            HTTPException: Если платеж не найден
        """
        # Получаем платеж
        payment = await self.payment_crud.get_payment(payment_id)
        if not payment:
            logger.warning("Payment not found", extra={"payment_id": str(payment_id)})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
            )

        try:
            # Получаем провайдера
            provider = self._get_provider(payment.provider)

            # Проверяем статус у провайдера
            if payment.provider_payment_id:
                provider_response = await provider.check_payment(
                    payment.provider_payment_id
                )

                # Обновляем статус платежа
                payment_update = SPaymentUpdate(
                    status=provider_response.get("status", payment.status),
                    payment_data=provider_response,
                )

                payment = await self.payment_crud.update_payment(
                    payment.id, payment_update
                )

                # Если платеж успешен, обновляем статус заказа
                if payment.status == PaymentStatus.SUCCEEDED.value:
                    await self._process_successful_payment(payment)

                # Если платеж отменен, тоже обновляем статус заказа
                elif payment.status in [
                    PaymentStatus.CANCELED.value,
                    PaymentStatus.FAILED.value,
                ]:
                    await self._process_failed_payment(payment)

            return payment

        except Exception as e:
            logger.error(
                "Failed to check payment status",
                extra={"payment_id": str(payment_id), "error": str(e)},
                exc_info=True,
            )
            # Возвращаем платеж без обновления
            return payment

    async def process_webhook(
        self, provider_name: str, webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обработка вебхука от платежной системы

        Args:
            provider_name: Название провайдера
            webhook_data: Данные вебхука

        Returns:
            Dict[str, Any]: Результат обработки

        Raises:
            HTTPException: При ошибке обработки вебхука
        """
        try:
            # Получаем провайдера
            provider = self._get_provider(provider_name)

            # Обрабатываем вебхук у провайдера
            payment_data = await provider.process_webhook(webhook_data)

            # Получаем ID платежа провайдера
            provider_payment_id = payment_data.get("provider_payment_id")
            if not provider_payment_id:
                logger.warning(
                    "No provider payment ID in webhook data",
                    extra={"provider": provider_name, "data": webhook_data},
                )
                return {"status": "error", "message": "No payment ID"}

            # Ищем платеж в нашей системе
            payment = await self.payment_crud.get_payment_by_provider_id(
                provider_name, provider_payment_id
            )

            if not payment:
                logger.warning(
                    "Payment not found for webhook",
                    extra={
                        "provider": provider_name,
                        "provider_payment_id": provider_payment_id,
                    },
                )
                return {"status": "error", "message": "Payment not found"}

            # Обновляем статус платежа
            payment_update = SPaymentUpdate(
                status=payment_data.get("status", payment.status),
                payment_data=webhook_data.get("object"),
            )

            updated_payment = await self.payment_crud.update_payment(
                payment.id, payment_update
            )

            # Если платеж успешен, обновляем статус заказа
            if updated_payment.status == PaymentStatus.SUCCEEDED.value:
                await self._process_successful_payment(updated_payment)

            # Если платеж отменен, тоже обновляем статус заказа
            elif updated_payment.status in [
                PaymentStatus.CANCELED.value,
                PaymentStatus.FAILED.value,
            ]:
                await self._process_failed_payment(updated_payment)

            logger.info(
                "Webhook processed successfully",
                extra={
                    "payment_id": str(payment.id),
                    "provider": provider_name,
                    "new_status": updated_payment.status,
                },
            )

            return {"status": "success", "payment_id": str(payment.id)}

        except ValueError as e:
            logger.error(
                "Invalid provider or webhook data",
                extra={"provider": provider_name, "error": str(e)},
                exc_info=True,
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(
                "Failed to process webhook",
                extra={
                    "provider": provider_name,
                    "error": str(e),
                    "data": webhook_data,
                },
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process webhook",
            )

    async def refund_payment(
        self, payment_id: UUID, amount: Optional[float] = None
    ) -> Payment:
        """
        Возврат платежа

        Args:
            payment_id: ID платежа
            amount: Сумма возврата (если None, то полный возврат)

        Returns:
            Payment: Обновленный платеж

        Raises:
            HTTPException: При ошибке возврата
        """
        # Получаем платеж
        payment = await self.payment_crud.get_payment(payment_id)
        if not payment:
            logger.warning("Payment not found", extra={"payment_id": str(payment_id)})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found"
            )

        # Проверяем статус платежа
        if payment.status != PaymentStatus.SUCCEEDED.value:
            logger.warning(
                "Cannot refund payment with status",
                extra={"payment_id": str(payment_id), "status": payment.status},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment cannot be refunded",
            )

        try:
            # Получаем провайдера
            provider = self._get_provider(payment.provider)

            # Выполняем возврат у провайдера
            if payment.provider_payment_id:
                refund_response = await provider.refund_payment(
                    payment.provider_payment_id, amount
                )

                # Обновляем статус платежа
                payment_update = SPaymentUpdate(
                    status=PaymentStatus.REFUNDED.value,
                    payment_data=(
                        {**payment.payment_data, "refund": refund_response}
                        if payment.payment_data
                        else {"refund": refund_response}
                    ),
                )

                payment = await self.payment_crud.update_payment(
                    payment.id, payment_update
                )

                # Обновляем статус заказа
                order = await self.order_crud.get_order(payment.order_id)
                if order and order.status == "paid":
                    await self.order_crud.update_status(order.id, "refunded")

                logger.info(
                    "Payment refunded successfully",
                    extra={
                        "payment_id": str(payment.id),
                        "provider": payment.provider,
                        "amount": amount if amount else float(payment.amount),
                    },
                )

            return payment

        except Exception as e:
            logger.error(
                "Failed to refund payment",
                extra={"payment_id": str(payment_id), "error": str(e)},
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refund payment",
            )

    async def _process_successful_payment(self, payment: Payment) -> None:
        """Обработка успешного платежа"""
        from sqlalchemy import update
        from app.models.order import Order
        from app.models.order_status import OrderStatus
        from app.models.user import User

        order = await self.order_crud.get_order(payment.order_id)
        if not order:
            logger.error(
                "Order not found for successful payment",
                extra={"payment_id": str(payment.id)},
            )
            return

        if order.status == OrderStatus.PAID.value:
            logger.info(
                "Order already marked as paid, skipping processing.",
                extra={"order_id": str(order.id)},
            )
            return

        order.status = OrderStatus.PAID.value
        order.payment_status = PaymentStatus.SUCCEEDED.value
        await self.session.commit()

        logger.info("Order status updated to PAID", extra={"order_id": str(order.id)})

        try:
            cdek_service = await get_cdek_service(self.session)
            user_crud = UserCRUD(self.session)
            user = await user_crud.get_by_id(
                order.user_id
            )

            if user:
                cdek_response = await cdek_service.create_cdek_order(order, user)
                if cdek_response and cdek_response.get("cdek_uuid"):
                    order.track_number = cdek_response.get(
                        "track_number"
                    ) or cdek_response.get("cdek_uuid")
                    await self.session.commit()
                    logger.info(
                        "Saved CDEK track number to order",
                        extra={
                            "order_id": str(order.id),
                            "track_number": order.track_number,
                        },
                    )
                else:
                    logger.error(
                        "Failed to get track number from CDEK",
                        extra={"order_id": str(order.id)},
                    )
            else:
                logger.error(
                    "User not found for CDEK order creation",
                    extra={"user_id": str(order.user_id)},
                )

        except Exception as e:
            logger.error(
                "Failed to create CDEK order after payment",
                extra={"order_id": str(order.id), "error": str(e)},
                exc_info=True,
            )

        # ... здесь будет вызов referral_service ...

        try:
            await self.discount_service.on_order_paid(order.user_id, order.id)
        except Exception as e:
            logger.error(
                "Failed to update user discount",
                extra={"order_id": str(order.id), "error": str(e)},
            )

        try:
            from app.crud.cart import CartCRUD

            cart_crud = CartCRUD(self.session)
            cart = await cart_crud.get_active_cart(order.user_id)
            if cart:
                await cart_crud.deactivate_cart(cart.id)
                logger.info(
                    "Cart deactivated after successful payment",
                    extra={"cart_id": str(cart.id)},
                )
        except Exception as e:
            logger.error(
                "Failed to deactivate cart",
                extra={"order_id": str(order.id), "error": str(e)},
            )

    async def _process_failed_payment(self, payment: Payment) -> None:
        """
        Обработка неудачного платежа

        Args:
            payment: Объект платежа
        """
        # Логика обработки неудачного платежа
        # Например, можно вернуть товары на склад или пометить заказ как требующий повторной оплаты
        logger.info(
            "Payment failed or canceled",
            extra={
                "payment_id": str(payment.id),
                "order_id": str(payment.order_id),
                "status": payment.status,
            },
        )

    async def create_widget_payment(
        self,
        order_id: UUID,
        provider_name: str,
        return_url: str,
        confirmation_type: str = "embedded",
    ) -> Tuple[Payment, str]:
        """
        Создание платежа для виджета с типом подтверждения embedded

        Args:
            order_id: ID заказа
            provider_name: Название провайдера
            return_url: URL возврата после оплаты
            confirmation_type: Тип подтверждения (по умолчанию "embedded")

        Returns:
            Tuple[Payment, str]: Созданный платеж и токен для инициализации виджета

        Raises:
            HTTPException: При ошибке создания платежа
        """
        # Получаем заказ
        order = await self.order_crud.get_order(order_id)
        if not order:
            logger.warning("Order not found", extra={"order_id": str(order_id)})
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        # Проверяем статус заказа
        if order.status not in ["pending", "created"]:
            logger.warning(
                "Invalid order status for payment",
                extra={"order_id": str(order_id), "status": order.status},
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order already paid or canceled",
            )

        try:
            # Получаем провайдера
            provider = self._get_provider(provider_name)

            # Создаем платеж с типом подтверждения embedded
            provider_response = await provider.create_payment(
                order, return_url, confirmation_type=confirmation_type
            )

            # Получаем токен подтверждения для виджета
            confirmation_token = provider_response.get("confirmation", {}).get(
                "confirmation_token"
            )
            if not confirmation_token:
                logger.error(
                    "No confirmation token in provider response",
                    extra={
                        "order_id": str(order_id),
                        "provider": provider_name,
                        "response": provider_response,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Payment system error",
                )

            # Создаем платеж в нашей БД
            payment_data = SPaymentCreate(
                order_id=order_id,
                provider=provider_name,
                amount=order.total,
                currency="RUB",
                payment_method=provider_response.get("payment_method", {}).get("type"),
            )

            payment = await self.payment_crud.create_payment(payment_data)

            # Обновляем данные платежа из ответа провайдера
            payment_update = SPaymentUpdate(
                provider_payment_id=provider_response.get("id"),
                status=provider_response.get("status", "pending"),
                confirmation_url=provider_response.get("confirmation", {}).get(
                    "confirmation_url"
                ),
                payment_data=provider_response,
            )

            payment = await self.payment_crud.update_payment(payment.id, payment_update)

            # Обновляем статус заказа и метод оплаты
            order.payment_method = provider_name
            order.payment_status = "pending"
            await self.session.commit()

            logger.info(
                "Widget payment created successfully",
                extra={
                    "payment_id": str(payment.id),
                    "order_id": str(order_id),
                    "provider": provider_name,
                    "confirmation_token": confirmation_token,
                },
            )

            return payment, confirmation_token

        except ValueError as e:
            logger.error("Invalid provider", extra={"error": str(e)}, exc_info=True)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(
                "Failed to create widget payment",
                extra={
                    "order_id": str(order_id),
                    "provider": provider_name,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment",
            )
