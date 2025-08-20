import { PAYMENT_PROVIDERS, PAYMENT_RETURN_URL_PATH } from "@/constants/payment";
import type { IPaymentResponse, IPaymentStatus, IWidgetPaymentResponse } from "@/types/payment";
import { logger } from "@/utils/logger";
import { apiClient } from "./httpClient";

/**
 * Сервис для работы с платежами
 */
export class PaymentService {
  /**
   * Создание платежа
   * @param orderId ID заказа для оплаты
   * @param provider Платежная система (по умолчанию "yookassa")
   * @returns Объект с информацией о платеже и URL для перенаправления
   */

  async createWidgetPayment(
    orderId: string,
    provider: string = PAYMENT_PROVIDERS.YOOKASSA,
  ): Promise<IWidgetPaymentResponse> {
    try {
      // Формируем URL для возврата после оплаты
      const returnUrl = `${window.location.origin}${PAYMENT_RETURN_URL_PATH}/${orderId}`;

      logger.info("Creating widget payment", {
        orderId,
        provider,
        returnUrl,
      });

      // Создаем параметры запроса с указанием типа confirmation
      const endpoint = `/payments/${orderId}/create-widget?return_url=${encodeURIComponent(returnUrl)}&provider=${encodeURIComponent(provider)}`;

      const response = await apiClient.post<IWidgetPaymentResponse>(endpoint, {});

      logger.info("Widget payment created successfully", {
        paymentId: response.payment_id,
        status: response.status,
        confirmationToken: response.confirmation_token,
      });

      return response;
    } catch (error) {
      logger.error("Failed to create widget payment", {
        orderId,
        provider,
        error,
      });
      throw error;
    }
  }

  // async createWidgetPayment(
  //   orderId: string,
  //   provider: string = PAYMENT_PROVIDERS.YOOKASSA,
  // ): Promise<IWidgetPaymentResponse> {
  //   try {
  //     // Формируем URL для возврата после оплаты
  //     const returnUrl = `${window.location.origin}${PAYMENT_RETURN_URL_PATH}${orderId}`

  //     logger.info('Creating widget payment', {
  //       orderId,
  //       provider,
  //       returnUrl,
  //     })

  //     // Создаем параметры запроса с указанием типа confirmation
  //     const endpoint = `/payments/${orderId}/create-widget?return_url=${encodeURIComponent(returnUrl)}&provider=${encodeURIComponent(provider)}`

  //     const response = await apiClient.post<IWidgetPaymentResponse>(endpoint, {})

  //     logger.info('Widget payment created successfully', {
  //       paymentId: response.payment_id,
  //       status: response.status,
  //       confirmationToken: response.confirmation_token,
  //     })

  //     return response
  //   } catch (error) {
  //     logger.error('Failed to create widget payment', {
  //       orderId,
  //       provider,
  //       error,
  //     })
  //     throw error
  //   }
  // }

  async createPayment(
    orderId: string,
    provider: string = PAYMENT_PROVIDERS.YOOKASSA,
  ): Promise<IPaymentResponse> {
    try {
      // Формируем URL для возврата после оплаты
      const returnUrl = `${window.location.origin}${PAYMENT_RETURN_URL_PATH}`;

      logger.info("Creating payment", {
        orderId,
        provider,
        returnUrl,
      });

      // Создаем параметры URL вручную
      const endpoint = `/payments/${orderId}/create?return_url=${encodeURIComponent(returnUrl)}&provider=${encodeURIComponent(provider)}`;

      // Используем post с пустым телом
      const response = await apiClient.post<IPaymentResponse>(endpoint, {});

      logger.info("Payment created successfully", {
        paymentId: response.payment_id,
        status: response.status,
      });

      return response;
    } catch (error) {
      logger.error("Failed to create payment", {
        orderId,
        provider,
        error,
      });
      throw error;
    }
  }

  /**
   * Проверка статуса платежа
   * @param paymentId ID платежа
   * @returns Объект с информацией о статусе платежа
   */
  async checkPaymentStatus(paymentId: string): Promise<IPaymentStatus> {
    try {
      logger.info("Checking payment status", { paymentId });

      const response = await apiClient.get<IPaymentStatus>(`/payments/${paymentId}/status`);

      logger.info("Payment status received", {
        paymentId,
        status: response.status,
      });

      return response;
    } catch (error) {
      logger.error("Failed to check payment status", {
        paymentId,
        error,
      });
      throw error;
    }
  }

  /**
   * Получение всех платежей для заказа
   * @param orderId ID заказа
   * @returns Массив платежей для заказа
   */
  async getOrderPayments(orderId: string): Promise<IPaymentStatus[]> {
    try {
      logger.info("Fetching order payments", { orderId });

      const response = await apiClient.get<{ items: IPaymentStatus[] }>(`/payments/order/${orderId}`);

      logger.info("Order payments received", {
        orderId,
        count: response.items.length,
      });

      return response.items;
    } catch (error) {
      logger.error("Failed to fetch order payments", {
        orderId,
        error,
      });
      throw error;
    }
  }
}

// Создаем и экспортируем экземпляр сервиса
export const paymentService = new PaymentService();
