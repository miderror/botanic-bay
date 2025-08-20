<script setup lang="ts">
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import ErrorIcon from "@/components/icons/ErrorIcon.vue";
import SuccessIcon from "@/components/icons/SuccessIcon.vue";
import { useNotification } from "@/composables/useNotification";
import { usePayment } from "@/composables/usePayment";
import { PAYMENT_PROVIDERS, PAYMENT_STATUSES } from "@/constants/payment";
import type { IPaymentResult } from "@/types/payment";
import { logger } from "@/utils/logger";
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

// Композаблы и служебные функции
const router = useRouter();
const route = useRoute();
const { showNotification } = useNotification();
const { handlePaymentReturn, initiatePayment } = usePayment();

// Состояние
const isLoading = ref(true);
const error = ref<string | null>(null);
const paymentResult = ref<IPaymentResult | null>(null);

// Обработка повторной оплаты
const handleRetry = async () => {
  // Получаем orderId из параметров или из paymentResult
  const orderId = (route.params.orderId as string) || paymentResult.value?.orderId;

  if (!orderId) {
    showNotification("Не удалось определить ID заказа для повторной оплаты", "error");
    return;
  }

  try {
    isLoading.value = true;
    error.value = null;

    logger.info("Retrying payment for order", { orderId });

    // Инициируем новый платеж для того же заказа
    await initiatePayment(orderId, PAYMENT_PROVIDERS.YOOKASSA);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Не удалось инициировать повторную оплату";
    error.value = message;
    showNotification(message, "error");

    logger.error("Failed to retry payment", {
      orderId,
      error: err,
    });

    isLoading.value = false;
  }
};

// Переход к списку заказов
const navigateToOrders = () => {
  router.push({ name: "profile-orders" });
};

// Получение сообщения в зависимости от статуса
const getStatusMessage = (status: string): string => {
  switch (status) {
    case PAYMENT_STATUSES.PENDING:
      return "Платеж создан, но еще не оплачен.";
    case PAYMENT_STATUSES.WAITING_FOR_CAPTURE:
      return "Деньги заблокированы на счете, ожидается подтверждение платежа.";
    case PAYMENT_STATUSES.CANCELED:
      return "Платеж отменен.";
    case PAYMENT_STATUSES.REFUNDED:
      return "Платеж возвращен.";
    case PAYMENT_STATUSES.FAILED:
      return "Произошла ошибка при проведении платежа.";
    case "not_found":
      return "Информация о платеже не найдена.";
    default:
      return "Статус платежа: " + status;
  }
};

// Проверка результата платежа при монтировании
onMounted(async () => {
  try {
    isLoading.value = true;
    error.value = null;

    // Получаем orderId из параметров маршрута
    const orderId = route.params.orderId;

    logger.info("Payment result page mounted", {
      query: route.query,
      params: route.params,
      orderId,
    });

    // Обрабатываем возврат с платежной страницы
    const result = await handlePaymentReturn();
    paymentResult.value = result;

    if (result.isSuccessful) {
      showNotification("Оплата успешно завершена!", "success");
      logger.info("Payment completed successfully", {
        orderId: result.orderId,
        paymentId: result.paymentId,
      });
    } else if (result.error) {
      error.value = result.error;
      logger.error("Payment verification failed", {
        status: result.status,
        error: result.error,
      });
    } else {
      logger.warn("Payment not successful", {
        status: result.status,
        orderId: result.orderId,
      });
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : "Ошибка при проверке статуса платежа";
    error.value = message;
    logger.error("Error in payment result page", { error: err });
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div class="payment-result-view">
    <div class="payment-result-container">
      <!-- Загрузка -->
      <LoadingSpinner v-if="isLoading" />

      <!-- Ошибка -->
      <div
        v-else-if="error"
        class="payment-error"
      >
        <ErrorIcon class="error-icon" />
        <h1 class="payment-title">Ошибка при проверке платежа</h1>
        <p class="payment-message">{{ error }}</p>
        <button
          @click="handleRetry"
          class="payment-button retry-button"
        >
          ПОПРОБОВАТЬ СНОВА
        </button>
        <button
          @click="navigateToOrders"
          class="payment-button secondary-button"
        >
          МОИ ЗАКАЗЫ
        </button>
      </div>

      <!-- Успешный платеж -->
      <div
        v-else-if="paymentResult && paymentResult.isSuccessful"
        class="payment-success"
      >
        <SuccessIcon class="success-icon" />
        <h1 class="payment-title">Оплата прошла успешно!</h1>
        <p class="payment-message">Ваш заказ успешно оплачен и передан в обработку.</p>
        <button
          @click="navigateToOrders"
          class="payment-button success-button"
        >
          МОИ ЗАКАЗЫ
        </button>
      </div>

      <!-- Неуспешный платеж -->
      <div
        v-else-if="paymentResult"
        class="payment-failed"
      >
        <ErrorIcon class="error-icon" />
        <h1 class="payment-title">Оплата не завершена</h1>
        <p class="payment-message">
          {{ getStatusMessage(paymentResult.status) }}
        </p>
        <button
          @click="handleRetry"
          class="payment-button retry-button"
        >
          ПОПРОБОВАТЬ СНОВА
        </button>
        <button
          @click="navigateToOrders"
          class="payment-button secondary-button"
        >
          МОИ ЗАКАЗЫ
        </button>
      </div>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/payment.css";
</style>
