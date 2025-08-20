import { PAYMENT_STATUSES } from "@/constants/payment";
import type { UUID } from "./common";

/**
 * Интерфейс ответа на создание платежа
 */
export interface IPaymentResponse {
  payment_id: UUID;
  confirmation_url: string;
  status: string;
}

/**
 * Интерфейс статуса платежа
 */
export interface IPaymentStatus {
  id: UUID;
  order_id: UUID;
  provider: string;
  provider_payment_id: string;
  status: PaymentStatusType;
  amount: string;
  currency: string;
  payment_method: string;
  created_at: string;
  updated_at: string;
  paid_at: string | null;
}

/**
 * Возможные статусы платежа
 */
export type PaymentStatusType =
  | typeof PAYMENT_STATUSES.PENDING
  | typeof PAYMENT_STATUSES.WAITING_FOR_CAPTURE
  | typeof PAYMENT_STATUSES.SUCCEEDED
  | typeof PAYMENT_STATUSES.CANCELED
  | typeof PAYMENT_STATUSES.REFUNDED
  | typeof PAYMENT_STATUSES.FAILED;

/**
 * Интерфейс результата платежа с дополнительной информацией
 */
export interface IPaymentResult {
  status: PaymentStatusType;
  orderId: UUID;
  paymentId: UUID;
  isSuccessful: boolean;
  error?: string;
}

// Структура для виджета
export interface IWidgetPaymentResponse extends IPaymentResponse {
  confirmation_token: string;
}

// Параметры для настройки виджета
export interface IWidgetOptions {
  confirmation_token: string;
  return_url: string;
  customization?: {
    modal?: boolean;
    payment_methods?: string[];
    colors?: {
      control_primary?: string;
      background?: string;
    };
  };
  error_callback: (error: unknown) => void;
}

export interface YooMoneyCheckoutWidget {
  new (options: {
    confirmation_token: string;
    return_url: string;
    customization?: {
      modal?: boolean;
      payment_methods?: string[];
    };
    error_callback: (error: unknown) => void;
  }): {
    render(containerId?: string): Promise<void>;
  };
}

declare global {
  interface Window {
    YooMoneyCheckoutWidget?: YooMoneyCheckoutWidget;
  }
}
