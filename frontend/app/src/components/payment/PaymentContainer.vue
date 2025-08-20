<script setup lang="ts">
import PaymentWidgetModal from "@/components/payment/PaymentWidgetModal.vue";
import { useNotification } from "@/composables/useNotification";
import { usePayment } from "@/composables/usePayment";
import { logger } from "@/utils/logger";

const paymentState = usePayment();
const { showNotification } = useNotification();

// Обработка ошибок оплаты
const handlePaymentError = (error: unknown) => {
  logger.error("Payment error in container", { error });
  showNotification("Произошла ошибка при оплате", "error");
};
</script>

<template>
  <div>
    <!-- Содержимое родительской страницы -->
    <slot></slot>

    <!-- Модальное окно с виджетом ЮКассы -->
    <PaymentWidgetModal
      v-if="paymentState.widgetState.isOpen"
      :isOpen="paymentState.widgetState.isOpen"
      :confirmationToken="paymentState.widgetState.confirmationToken"
      :returnUrl="paymentState.widgetState.returnUrl"
      @update:isOpen="paymentState.widgetState.isOpen = $event"
      @close="paymentState.handleWidgetClose"
      @success="paymentState.handleWidgetSuccess"
      @error="handlePaymentError"
    />
  </div>
</template>
