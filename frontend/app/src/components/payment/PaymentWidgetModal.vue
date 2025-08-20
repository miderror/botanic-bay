<script setup lang="ts">
import BaseModal from "@/components/common/BaseModal.vue";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import { logger } from "@/utils/logger";
import { onMounted, ref } from "vue";

defineProps<{
  isOpen: boolean;
  confirmationToken: string;
  returnUrl: string;
}>();

const emit = defineEmits<{
  (e: "update:isOpen", value: boolean): void;
  (e: "success"): void;
  (e: "error", error: unknown): void;
  (e: "close"): void;
}>();

const isLoading = ref(true);

// Обработчик закрытия модального окна
const handleClose = () => {
  logger.debug("PaymentWidgetModal: closing modal");
  emit("update:isOpen", false);
  emit("close");
};

// Обработчик ошибок виджета
const handleWidgetError = (event: CustomEvent) => {
  logger.error("PaymentWidgetModal: widget error event received", event.detail);
  emit("error", event.detail.error);
  handleClose();
};

// При монтировании компонента добавляем слушатель события ошибки
onMounted(() => {
  window.addEventListener("payment-widget-error", handleWidgetError as EventListener);
  logger.debug("PaymentWidgetModal: mounted and event listener added");
  isLoading.value = false;
});

// При размонтировании компонента удаляем слушатель события
onMounted(() => {
  return () => {
    window.removeEventListener("payment-widget-error", handleWidgetError as EventListener);
    logger.debug("PaymentWidgetModal: unmounted and event listener removed");
  };
});
</script>

<template>
  <BaseModal
    :modelValue="isOpen"
    @update:modelValue="handleClose"
    title="Оплата заказа"
  >
    <div
      class="payment-widget-container"
      id="yookassa-payment-form"
    >
      <!-- Сюда будет рендериться виджет ЮКассы -->
      <LoadingSpinner v-if="isLoading" />
    </div>
  </BaseModal>
</template>

<style>
@import "@/assets/styles/payment.css";
</style>
