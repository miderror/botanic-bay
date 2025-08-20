export const PAYMENT_STATUSES = {
  // Статусы платежей
  PENDING: "pending",
  WAITING_FOR_CAPTURE: "waiting_for_capture",
  SUCCEEDED: "succeeded",
  CANCELED: "canceled",
  REFUNDED: "refunded",
  FAILED: "failed",
};

export const PAYMENT_PROVIDERS = {
  // Провайдеры платежей
  YOOKASSA: "yookassa",
};

// Таймаут для проверки платежа (в миллисекундах)
export const PAYMENT_CHECK_TIMEOUT = 5000;

// URL для возврата после оплаты
export const PAYMENT_RETURN_URL_PATH = "/payment/result";

// Новые константы для виджета ЮКассы
export const YOOKASSA_WIDGET_URL = "https://yookassa.ru/checkout-widget/v1/checkout-widget.js";

export const YOOKASSA_CONFIRMATION_TYPES = {
  REDIRECT: "redirect",
  EMBEDDED: "embedded",
};
