<script setup lang="ts">
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import CloseButton from "@/components/icons/CloseButton.vue";
import ErrorIcon from "@/components/icons/ErrorIcon.vue";
import { useNotification } from "@/composables/useNotification";
import { usePayment } from "@/composables/usePayment";
import { PAYMENT_STATUSES } from "@/constants/payment";
import { logger } from "@/utils/logger";
import { onMounted, onUnmounted, ref, watch } from "vue";

interface Props {
  isOpen: boolean;
  paymentUrl: string;
  paymentId: string;
  orderId: string;
}

interface Emits {
  (e: "update:isOpen", value: boolean): void;
  (e: "paymentComplete", success: boolean): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// Composables
const { checkPaymentStatus } = usePayment();
const { showNotification } = useNotification();

// Refs
const paymentFrame = ref<HTMLIFrameElement | null>(null);
const isLoading = ref(true);
const error = ref<string | null>(null);
const isPolling = ref(false);
let pollingInterval: number | null = null;

// Константы для поллинга
const POLLING_INTERVAL = 3000; // 3 секунды
const MAX_POLLING_ATTEMPTS = 20; // Максимум 1 минута (20 * 3 секунды)
let pollingAttempts = 0;

// Обработчик загрузки iframe
const handleIframeLoad = () => {
  isLoading.value = false;

  // Запускаем поллинг статуса платежа
  startPolling();

  logger.info("Payment iframe loaded", {
    paymentId: props.paymentId,
    url: props.paymentUrl,
  });
};

// Перезагрузка iframe
const reload = () => {
  if (paymentFrame.value) {
    isLoading.value = true;
    error.value = null;

    try {
      paymentFrame.value.src = props.paymentUrl;
    } catch {
      handleFrameError("Не удалось перезагрузить платежную форму");
    }
  }
};

// Обработка ошибок iframe
const handleFrameError = (message: string) => {
  isLoading.value = false;
  error.value = message;

  logger.error("Payment iframe error", {
    message,
    paymentId: props.paymentId,
  });
};

// Закрытие модального окна
const handleClose = () => {
  if (isPolling.value) {
    const confirmClose = confirm(
      "Проверка статуса платежа не завершена. Вы уверены, что хотите закрыть окно?",
    );
    if (!confirmClose) return;
  }

  stopPolling();
  emit("update:isOpen", false);
};

// Запуск поллинга статуса платежа
const startPolling = () => {
  if (pollingInterval) return;

  isPolling.value = true;
  pollingAttempts = 0;

  pollingInterval = window.setInterval(async () => {
    pollingAttempts++;

    try {
      logger.debug("Polling payment status", {
        paymentId: props.paymentId,
        attempt: pollingAttempts,
      });

      const result = await checkPaymentStatus(props.paymentId);

      if (result.isSuccessful) {
        // Платеж успешен
        stopPolling();
        showNotification("Оплата успешно завершена!", "success");
        emit("paymentComplete", true);
        emit("update:isOpen", false);
      } else if (result.status === PAYMENT_STATUSES.CANCELED || result.status === PAYMENT_STATUSES.FAILED) {
        // Платеж отменен или произошла ошибка
        stopPolling();
        showNotification("Оплата не была завершена", "error");
        emit("paymentComplete", false);

        // Оставляем модальное окно открытым, чтобы пользователь мог увидеть сообщение об ошибке
      }

      // Останавливаем поллинг после максимального количества попыток
      if (pollingAttempts >= MAX_POLLING_ATTEMPTS) {
        stopPolling();
        logger.warn("Max polling attempts reached", {
          paymentId: props.paymentId,
          attempts: pollingAttempts,
        });

        // Спрашиваем пользователя, хочет ли он продолжить проверку
        const continuePolling = confirm(
          "Проверка статуса платежа занимает больше времени, чем ожидалось. Продолжить проверку?",
        );

        if (continuePolling) {
          // Перезапускаем поллинг
          startPolling();
        } else {
          emit("update:isOpen", false);
        }
      }
    } catch (err) {
      logger.error("Error polling payment status", {
        paymentId: props.paymentId,
        attempt: pollingAttempts,
        error: err,
      });

      // При ошибке поллинга продолжаем пытаться (не останавливаем интервал)
    }
  }, POLLING_INTERVAL);
};

// Остановка поллинга
const stopPolling = () => {
  if (pollingInterval) {
    window.clearInterval(pollingInterval);
    pollingInterval = null;
    isPolling.value = false;
  }
};

// Жизненный цикл
onMounted(() => {
  logger.info("Payment modal mounted", {
    paymentId: props.paymentId,
    paymentUrl: props.paymentUrl,
  });
});

onUnmounted(() => {
  stopPolling();
  logger.info("Payment modal unmounted", {
    paymentId: props.paymentId,
  });
});

// Следим за изменением URL платежа
watch(
  () => props.paymentUrl,
  (newUrl) => {
    if (paymentFrame.value && newUrl) {
      isLoading.value = true;
      error.value = null;
      paymentFrame.value.src = newUrl;
    }
  },
);
</script>

<template>
  <div
    class="payment-modal-overlay"
    v-if="isOpen"
  >
    <div class="payment-modal-container">
      <div class="payment-modal-header">
        <h2 class="payment-modal-title">Оплата заказа</h2>
        <button
          class="payment-modal-close"
          @click="handleClose"
        >
          <CloseButton />
        </button>
      </div>

      <div class="payment-modal-body">
        <div
          v-if="isLoading"
          class="payment-loading"
        >
          <LoadingSpinner />
          <p class="payment-loading-text">Загрузка платежной формы...</p>
        </div>

        <div
          v-else-if="error"
          class="payment-error"
        >
          <ErrorIcon class="error-icon" />
          <p class="payment-error-text">{{ error }}</p>
          <button
            class="payment-button retry-button"
            @click="reload"
          >
            ПОПРОБОВАТЬ СНОВА
          </button>
        </div>

        <iframe
          v-else
          ref="paymentFrame"
          :src="paymentUrl"
          class="payment-iframe"
          @load="handleIframeLoad"
          sandbox="allow-forms allow-scripts allow-same-origin allow-top-navigation allow-popups"
        ></iframe>
      </div>

      <!-- Блок с информацией о статусе платежа -->
      <div
        v-if="isPolling"
        class="payment-status-info"
      >
        <div class="payment-status-spinner">
          <LoadingSpinner small />
        </div>
        <p class="payment-status-text">Проверка статуса платежа...</p>
      </div>
    </div>
  </div>
</template>

<style>
.payment-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.payment-modal-container {
  width: 90%;
  max-width: 480px;
  height: 80vh;
  max-height: 800px;
  background-color: white;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
}

.payment-modal-header {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.payment-modal-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--payment-text-primary);
  text-align: center;
  font-family: "Open Sans Hebrew", sans-serif;
}

.payment-modal-close {
  position: absolute;
  right: 12px;
  top: 12px;
  background: none;
  border: none;
  cursor: pointer;
}

.payment-modal-body {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.payment-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.payment-loading,
.payment-error {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: white;
  gap: 16px;
  padding: 20px;
}

.payment-loading-text,
.payment-error-text {
  text-align: center;
  color: var(--payment-text-secondary);
  font-family: "Pontano Sans", sans-serif;
  font-size: 14px;
}

.payment-button {
  padding: 10px 30px;
  border-radius: 100px;
  font-size: 12px;
  font-family: "Inter", sans-serif;
  font-weight: 700;
  background-color: var(--payment-text-primary);
  color: white;
  border: none;
  cursor: pointer;
  text-transform: uppercase;
}

.payment-status-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  gap: 10px;
  border-top: 1px solid #eee;
}

.payment-status-text {
  margin: 0;
  font-size: 12px;
  color: var(--payment-text-primary);
  font-family: "Pontano Sans", sans-serif;
}

.error-icon {
  width: 40px;
  height: 40px;
}

.error-icon path {
  fill: var(--payment-error);
}
</style>
