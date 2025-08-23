import type { UUID } from "./common";

/**
 * Методы доставки
 */
export enum DeliveryMethod {
  PICKUP = "pickup", // Самовывоз
  COURIER = "courier", // Курьер
}

/**
 * Методы оплаты
 */
export enum PaymentMethod {
  CARD = "card", // Банковская карта
  ONLINE = "online", // Онлайн оплата
  CASHLESS = "cashless", // Безналичный расчет
  YOOKASSA = "yookassa", // ЮKassa оплата
}

/**
 * Статусы заказа
 */
export enum OrderStatus {
  PENDING = "pending", // Ожидает оплаты
  PAID = "paid", // Оплачен
  PROCESSING = "processing", // В обработке
  SHIPPED = "shipped", // Отправлен
  DELIVERED = "delivered", // Доставлен
  CANCELLED = "cancelled", // Отменен
}

/**
 * Интерфейс для создания заказа
 */
export interface ICreateOrder {
  delivery_point_id?: UUID;
  address_id?: UUID;
  delivery_method: DeliveryMethod;
  payment_method: PaymentMethod;
  promo_code?: string | null;
}

/**
 * Интерфейс элемента заказа
 */
export interface IOrderItem {
  id: UUID;
  product_id: UUID;
  product_name: string;
  quantity: number;
  price: number;
  subtotal: number;
  image_url?: string;
}

/**
 * Интерфейс заказа
 */
export interface IOrder {
  id: UUID;
  status: OrderStatus;
  items: IOrderItem[];
  delivery_method: DeliveryMethod;
  delivery_point?: string;
  delivery_to_location?: IDeliveryToLocation;
  delivery_cost: number;
  payment_method: PaymentMethod;
  payment_status: string;
  subtotal: number;
  total: number;
  created_at: string;
  updated_at: string;
}

export interface IDeliveryToLocation {
  address: string;
  latitude: number;
  longitude: number;
}

/**
 * Интерфейс метода оплаты
 */
export interface IPaymentMethod {
  id: PaymentMethod;
  name: string;
  icon: string;
  is_available: boolean;
}

/**
 * Интерфейс точки самовывоза
 */
export interface IUserDeliveryPoint {
  id: string;
  name: string;
  address: string;
}

/**
 * Интерфейс адреса доставки
 */
export interface IUserAddress {
  id?: string;
  latitude: number;
  longitude: number;
  address: string;
  apartment: number;
  entrance?: number;
  floor?: number;
  intercom_code?: number;
  // is_default: boolean;
}
