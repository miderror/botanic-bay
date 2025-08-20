# backend/app/api/routes/payment.py
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps import get_current_admin, get_current_user, get_payment_service
from app.core.constants import YOOKASSA_CONFIRMATION_TYPES
from app.core.logger import logger
from app.models.user import User
from app.schemas.payment import SPayment, SPaymentResponse, SWidgetPaymentResponse
from app.services.payment.payment_service import PaymentService

router = APIRouter()


@router.post("/{order_id}/create-widget", response_model=SWidgetPaymentResponse)
async def create_widget_payment(
    order_id: UUID,
    provider: str = Query("yookassa", description="Платежная система"),
    return_url: str = Query(..., description="URL для возврата после оплаты"),
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
) -> Dict[str, Any]:
    """
    Создание платежа с использованием виджета (embedded confirmation)
    """
    try:
        logger.info(
            "Creating widget payment",
            extra={
                "order_id": str(order_id),
                "provider": provider,
                "user_id": str(current_user.id),
            },
        )

        # Создаем платеж с типом подтверждения embedded
        payment, confirmation_token = await payment_service.create_widget_payment(
            order_id=order_id,
            provider_name=provider,
            return_url=return_url,
            confirmation_type=YOOKASSA_CONFIRMATION_TYPES["EMBEDDED"],
        )

        logger.info(
            "Widget payment created",
            extra={
                "payment_id": str(payment.id),
                "order_id": str(order_id),
                "has_token": bool(confirmation_token),
            },
        )

        # Формируем ответ с токеном для виджета
        return {
            "payment_id": payment.id,
            "confirmation_token": confirmation_token,
            "status": payment.status,
        }

    except Exception as e:
        logger.error(
            "Failed to create widget payment",
            extra={"order_id": str(order_id), "provider": provider, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment",
        )


@router.post("/{order_id}/create", response_model=SPaymentResponse)
async def create_payment(
    order_id: UUID,
    return_url: str = Query(..., description="URL для возврата после оплаты"),
    provider: str = Query("yookassa", description="Платежная система"),
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Создание платежа для заказа

    Args:
        order_id: ID заказа
        return_url: URL для возврата после оплаты
        provider: Платежная система

    Returns:
        SPaymentResponse: Данные для оплаты
    """
    payment, confirmation_url = await payment_service.create_payment(
        order_id, provider, return_url
    )

    return SPaymentResponse(
        payment_id=payment.id, confirmation_url=confirmation_url, status=payment.status
    )


@router.get("/{payment_id}/status", response_model=SPayment)
async def check_payment_status(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Проверка статуса платежа

    Args:
        payment_id: ID платежа

    Returns:
        SPayment: Данные платежа
    """
    payment = await payment_service.check_payment_status(payment_id)
    return payment


@router.post("/webhooks/yookassa", status_code=status.HTTP_200_OK)
async def yookassa_webhook(
    request: Request, payment_service: PaymentService = Depends(get_payment_service)
):
    """
    Вебхук для уведомлений от ЮКассы

    Args:
        request: Запрос FastAPI

    Returns:
        Dict[str, Any]: Результат обработки
    """
    try:
        # Получаем данные запроса
        data = await request.json()

        # Проверяем и обрабатываем вебхук через сервис
        logger.info(
            "Received YooKassa webhook",
            extra={
                "event": data.get("event"),
                "object_id": data.get("object", {}).get("id"),
            },
        )

        result = await payment_service.process_webhook("yookassa", data)
        return result

    except Exception as e:
        logger.error(
            "YooKassa webhook processing error", extra={"error": str(e)}, exc_info=True
        )
        # Возвращаем 200 OK даже при ошибке, чтобы ЮКасса не делала повторных попыток
        # ЮКасса рекомендует всегда возвращать 200 OK независимо от результата обработки
        return {"status": "error", "message": str(e)}


@router.post("/{payment_id}/refund", response_model=SPayment)
async def refund_payment(
    payment_id: UUID,
    amount: Optional[float] = Query(
        None, description="Сумма возврата (если не указана, то полный возврат)"
    ),
    current_user: User = Depends(get_current_admin),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Возврат платежа (только для администраторов)

    Args:
        payment_id: ID платежа
        amount: Сумма возврата (если None, то полный возврат)

    Returns:
        SPayment: Обновленный платеж
    """
    payment = await payment_service.refund_payment(payment_id, amount)
    return payment


@router.get("/order/{order_id}", response_model=list[SPayment])
async def get_order_payments(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Получение всех платежей для заказа

    Args:
        order_id: ID заказа

    Returns:
        list[SPayment]: Список платежей
    """
    payments = await payment_service.payment_crud.get_order_payments(order_id)
    return payments
