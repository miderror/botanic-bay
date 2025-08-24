import { useNotification } from "@/composables/useNotification";
import {
  PAYMENT_PROVIDERS,
  PAYMENT_RETURN_URL_PATH,
  PAYMENT_STATUSES,
  YOOKASSA_WIDGET_URL,
} from "@/constants/payment";
import { orderService } from "@/services/orderService"; // Добавим импорт orderService
import { paymentService } from "@/services/paymentService";
import { useCartStore } from "@/stores/cart"; // Добавим импорт cartStore
import type { IPaymentResult, IPaymentStatus } from "@/types/payment";
import { logger } from "@/utils/logger";
import { computed, onUnmounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { useCheckoutStore } from "@/stores/checkout";

export function usePayment() {
  const router = useRouter();
  const { showNotification } = useNotification();
  const cartStore = useCartStore(); // Инициализируем cartStore
  const checkoutStore = useCheckoutStore();

  // Состояние
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const currentPaymentId = ref<string | null>(null);
  const paymentStatus = ref<IPaymentStatus | null>(null);
  const scriptElement = ref<HTMLScriptElement | null>(null);

  // Новое состояние для виджета
  const widgetState = reactive({
    isOpen: false,
    confirmationToken: "",
    returnUrl: "",
    isInitializing: false,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    widgetInstance: null as any,
  });

  // Функция для извлечения orderId из URL
  const extractOrderIdFromUrl = (url: string): string | null => {
    if (!url) return null;
    const parts = url.split("/");
    return parts[parts.length - 1] || null;
  };

  // Получаем ID платежа из localStorage
  const getStoredPaymentId = (): string | null => {
    try {
      return localStorage.getItem("currentPaymentId");
    } catch (err) {
      logger.error("Failed to get payment ID from localStorage", { error: err });
      return null;
    }
  };

  // Сохраняем ID платежа в localStorage
  const storePaymentId = (paymentId: string): void => {
    try {
      localStorage.setItem("currentPaymentId", paymentId);
      currentPaymentId.value = paymentId;
    } catch (err) {
      logger.error("Failed to store payment ID to localStorage", {
        paymentId,
        error: err,
      });
    }
  };

  // Удаляем ID платежа из localStorage
  const clearStoredPaymentId = (): void => {
    try {
      localStorage.removeItem("currentPaymentId");
      currentPaymentId.value = null;
    } catch (err) {
      logger.error("Failed to clear payment ID from localStorage", { error: err });
    }
  };

  // Проверяем успешность платежа по статусу
  const isPaymentSuccessful = computed(() => {
    return paymentStatus.value?.status === PAYMENT_STATUSES.SUCCEEDED;
  });

  // Создание платежа и переход на страницу оплаты
  const initiatePayment = async (
    orderId: string,
    provider: string = PAYMENT_PROVIDERS.YOOKASSA,
  ): Promise<boolean> => {
    try {
      isLoading.value = true;
      error.value = null;

      logger.info("Initiating payment", { orderId, provider });

      // Создаем платеж через API
      const payment = await paymentService.createPayment(orderId, provider);

      // Сохраняем ID платежа для последующей проверки
      storePaymentId(payment.payment_id);

      // Перенаправляем пользователя на страницу оплаты
      window.location.href = payment.confirmation_url;

      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Ошибка при создании платежа";
      error.value = message;
      showNotification(message, "error");

      logger.error("Payment initiation failed", {
        orderId,
        provider,
        error: err,
      });

      return false;
    } finally {
      isLoading.value = false;
    }
  };

  // Проверка статуса платежа
  const checkPaymentStatus = async (paymentId?: string): Promise<IPaymentResult> => {
    try {
      isLoading.value = true;
      error.value = null;

      // Если ID платежа не передан, пытаемся получить из хранилища
      const id = paymentId || getStoredPaymentId();

      if (!id) {
        throw new Error("ID платежа не найден");
      }

      logger.info("Checking payment status", { paymentId: id });

      // Получаем статус платежа
      const status = await paymentService.checkPaymentStatus(id);
      paymentStatus.value = status;

      const result: IPaymentResult = {
        status: status.status,
        orderId: status.order_id,
        paymentId: status.id,
        isSuccessful: status.status === PAYMENT_STATUSES.SUCCEEDED,
      };

      // Очищаем ID платежа после проверки
      if (result.isSuccessful) {
        clearStoredPaymentId();
      }

      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Ошибка при проверке статуса платежа";
      error.value = message;

      logger.error("Failed to check payment status", {
        paymentId,
        error: err,
      });

      return {
        status: "failed",
        orderId: "",
        paymentId: paymentId || "",
        isSuccessful: false,
        error: message,
      };
    } finally {
      isLoading.value = false;
    }
  };

  // Обработка возврата с платежной страницы
  const handlePaymentReturn = async (): Promise<IPaymentResult> => {
    try {
      const paymentId = getStoredPaymentId();

      if (!paymentId) {
        throw new Error("ID платежа не найден после возврата с платежной страницы");
      }

      // Проверяем статус платежа
      const result = await checkPaymentStatus(paymentId);
      if (result.isSuccessful) {
        clearStoredPaymentId();
    }

    return result; 
    } catch (err) {
      const message = err instanceof Error ? err.message : "Ошибка при обработке возврата после оплаты";
      error.value = message;

      logger.error("Payment return handling failed", { error: err });

      return {
        status: "failed",
        orderId: "",
        paymentId: getStoredPaymentId() || "",
        isSuccessful: false,
        error: message,
      };
    }
  };

  // Загрузка скрипта виджета ЮКассы
  const loadYookassaScript = async (): Promise<void> => {
    if (window.YooMoneyCheckoutWidget) {
      logger.debug("loadYookassaScript: YooKassa widget script already loaded");
      return Promise.resolve();
    }

    // Проверяем валидность URL
    if (!YOOKASSA_WIDGET_URL || typeof YOOKASSA_WIDGET_URL !== "string") {
      throw new Error("loadYookassaScript: Invalid YooKassa script URL");
    }

    logger.info("Loading YooKassa widget script", { scriptUrl: YOOKASSA_WIDGET_URL });

    return new Promise<void>((resolve, reject) => {
      try {
        // Удаляем старый скрипт, если есть
        if (scriptElement.value && document.head.contains(scriptElement.value)) {
          document.head.removeChild(scriptElement.value);
          scriptElement.value = null;
        }

        // Создаем новый элемент скрипта с проверками
        const script = document.createElement("script");
        if (!script) {
          throw new Error("loadYookassaScript: Failed to create script element");
        }

        script.src = YOOKASSA_WIDGET_URL;
        script.async = true;
        script.crossOrigin = "anonymous";

        script.onload = () => {
          logger.info("loadYookassaScript: YooKassa widget script loaded successfully");
          scriptElement.value = script;
          resolve();
        };

        script.onerror = (e) => {
          logger.error("loadYookassaScript: Failed to load YooKassa script", { error: e });
          reject(new Error("loadYookassaScript: Failed to load YooKassa script"));
        };

        if (document.head) {
          document.head.appendChild(script);
        } else {
          throw new Error("loadYookassaScript: Document head not available");
        }
      } catch (error) {
        logger.error("Error in loadYookassaScript", { error });
        reject(error);
      }
    });
  };

  // Инициализация виджета ЮКассы
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const initializeYookassaWidget = (token: string, returnUrl: string): any => {
    if (!window.YooMoneyCheckoutWidget) {
      throw new Error("YooKassa widget script not loaded");
    }

    logger.info("Initializing YooKassa widget", { token, returnUrl });

    const checkout = new window.YooMoneyCheckoutWidget({
      confirmation_token: token,
      return_url: returnUrl, // Убедимся, что return_url передается
      customization: {
        modal: true,
      },
      error_callback: function (error: any) {
        logger.error("YooKassa widget error", { error });
        handleWidgetError(error);
      },
    });

    setupWidgetEventHandlers(checkout, returnUrl);
    return checkout;
  };

  // Настройка обработчиков событий виджета
  const setupWidgetEventHandlers = (checkout: any, returnUrl: string) => {
    const orderId = extractOrderIdFromUrl(returnUrl) || "";

    const navigateToResult = (success: boolean) => {
        router.replace({ 
            name: "payment-result", 
            params: { orderId },
            query: { status: success ? 'success' : 'fail' } 
        });
    };

    checkout.on("success", async () => {
      logger.info("YooKassa widget success event", { orderId });
      closeWidget();
      navigateToResult(true);
    });

    checkout.on("fail", () => {
      logger.warn("YooKassa widget fail event", { orderId });
      closeWidget();
      navigateToResult(false);
    });
    
  };

  // Открытие виджета ЮКассы
  const openYookassaWidget = async (token: string, returnUrl: string): Promise<void> => {
    try {
      widgetState.isInitializing = true;

      // Загружаем скрипт ЮКассы
      await loadYookassaScript();

      // Инициализируем виджет
      widgetState.widgetInstance = initializeYookassaWidget(token, returnUrl);

      // Рендерим виджет
      await widgetState.widgetInstance.render();

      checkoutStore.isPaymentProcessing = false;

      logger.info("YooKassa widget rendered successfully");

      // Находим iframe с виджетом ЮКассы и добавляем ему атрибуты разрешений
      const iframes = document.querySelectorAll("iframe");
      iframes.forEach((iframe) => {
        if (iframe.src.includes("yoomoney.ru")) {
          iframe.setAttribute("allow", "camera; microphone; payment");
        }
      });

      widgetState.isOpen = true;
      widgetState.isInitializing = false;
    } catch (error) {
      widgetState.isInitializing = false;
      checkoutStore.isPaymentProcessing = false;
      logger.error("YooKassa widget render error", { error });

      // Показываем ошибку пользователю
      showNotification("Не удалось открыть платежную форму", "error");

      // Распространяем ошибку дальше
      handleWidgetError(error);
      throw error;
    }
  };

  // Закрытие виджета
  const closeWidget = () => {
    try {
      if (widgetState.widgetInstance) {
        widgetState.widgetInstance.destroy();
        widgetState.widgetInstance = null;
      }

      widgetState.isOpen = false;
      widgetState.confirmationToken = "";
      widgetState.returnUrl = "";
      
      checkoutStore.isPaymentProcessing = false;
      
      logger.debug("Widget closed and state reset");
    } catch (error) {
      logger.error("Error closing widget", { error });
    }
  };

  // Инициирование платежа через виджет
  const initiateWidgetPayment = async (
    orderId: string,
    provider: string = PAYMENT_PROVIDERS.YOOKASSA,
  ): Promise<boolean> => {
    try {
      isLoading.value = true;
      error.value = null;

      logger.info("Initiating widget payment", { orderId, provider });

      const returnUrl = `${window.location.origin}${PAYMENT_RETURN_URL_PATH}/${orderId}`;

      const payment = await paymentService.createWidgetPayment(orderId, provider);

      storePaymentId(payment.payment_id);

      logger.info("Payment created, opening widget", {
        paymentId: payment.payment_id,
        hasToken: !!payment.confirmation_token,
      });

      widgetState.confirmationToken = payment.confirmation_token;
      widgetState.returnUrl = returnUrl;

      await openYookassaWidget(payment.confirmation_token, returnUrl);
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Ошибка при создании платежа";
      error.value = message;
      showNotification(message, "error");

      logger.error("Widget payment initiation failed", {
        orderId,
        provider,
        error: err,
      });

      return false;
    } finally {
      isLoading.value = false;
    }
  };

  // Обработчик закрытия виджета пользователем
  const handleWidgetClose = async () => {
    try {
      // Извлекаем orderId из returnUrl
      const orderId = extractOrderIdFromUrl(widgetState.returnUrl);

      if (orderId) {
        // Вызываем API для отмены заказа
        await orderService.cancelOrder(orderId);
        logger.info("Order cancelled after manual widget close", { orderId });
      }
    } catch (error) {
      logger.error("Failed to cancel order on widget close", { error });
    } finally {
      closeWidget();
      logger.info("Payment widget closed by user");
    }
  };

  // Обработчик успешной оплаты
  const handleWidgetSuccess = async () => {
    const paymentId = getStoredPaymentId();

    if (paymentId) {
      try {
        // Проверяем статус платежа
        const result = await checkPaymentStatus(paymentId);

        if (result.isSuccessful) {
          showNotification("Оплата успешно завершена!", "success");
          clearStoredPaymentId();

          // Очищаем корзину только при успешной оплате
          try {
            await cartStore.clearCart();
            logger.info("Cart cleared after successful payment");
          } catch (cartError) {
            logger.error("Failed to clear cart after successful payment", { error: cartError });
          }

          // Перенаправляем на страницу с результатом
          router.push({
            name: "payment-result",
            params: { orderId: result.orderId },
          });
        }
      } catch (error) {
        logger.error("Failed to check payment status after widget close", { error });
      }
    }

    closeWidget();
  };

  // Обработчик ошибки виджета
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleWidgetError = (error: any) => {
    logger.error("Payment widget error", { error });
    showNotification("Произошла ошибка при работе с платежной формой", "error");

    // Закрываем виджет в случае ошибки
    closeWidget();

    // Генерируем событие ошибки для компонентов, которые могут его перехватить
    window.dispatchEvent(
      new CustomEvent("payment-widget-error", {
        detail: {
          error: error instanceof Error ? error.message : "Ошибка виджета ЮКассы",
        },
      }),
    );
  };

  // Очистка ресурсов при размонтировании
  onUnmounted(() => {
    closeWidget();

    // Удаляем скрипт ЮКассы при размонтировании компонента
    if (scriptElement.value && document.head.contains(scriptElement.value)) {
      document.head.removeChild(scriptElement.value);
      scriptElement.value = null;
    }
  });

  return {
    // Состояние
    isLoading,
    error,
    currentPaymentId,
    paymentStatus,
    isPaymentSuccessful,

    // Методы для платежей с редиректом
    initiatePayment,
    checkPaymentStatus,
    handlePaymentReturn,
    storePaymentId,
    clearStoredPaymentId,
    getStoredPaymentId,

    // Состояние виджета
    widgetState,

    // Методы для виджета
    initiateWidgetPayment,
    openYookassaWidget,
    closeWidget,
    handleWidgetClose,
    handleWidgetSuccess,
    handleWidgetError,
    loadYookassaScript,

    // Вспомогательные функции
    extractOrderIdFromUrl,
  };
}
