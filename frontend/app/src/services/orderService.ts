import type { IDeliveryPoint } from "@/types/cdek.ts";
import type { UUID } from "@/types/common.ts";
import type { ICreateOrder, IOrder, IPaymentMethod, IUserAddress, IUserDeliveryPoint } from "@/types/order";
import { PaymentMethod } from "@/types/order";
import { logger } from "@/utils/logger";
import { apiClient } from "./httpClient";

export class OrderService {
  /**
   * Получение сохраненных адресов пользователя
   */
  async getAddresses(): Promise<IUserAddress[]> {
    try {
      logger.info("Fetching user addresses");
      return await apiClient.get(`/orders/addresses`);
    } catch (error) {
      logger.error("Failed to fetch user addresses", { error });
      throw error;
    }
  }

  async saveAddress(addressData: IUserAddress): Promise<IUserAddress> {
    try {
      logger.info("Saving user addresses", { addressData });
      return await apiClient.post<IUserAddress>(`/orders/addresses`, addressData);
    } catch (error) {
      logger.error("Failed to save user address", { error });
      throw error;
    }
  }

  async updateAddress(addressId: string, addressData: IUserAddress): Promise<IUserAddress> {
    try {
      logger.info("Updating user address", { addressId, addressData });
      return await apiClient.patch<IUserAddress>(`/orders/addresses/${addressId}`, addressData);
    } catch (error) {
      logger.error("Failed to update user address", { error });
      throw error;
    }
  }

  async deleteAddress(address_id: UUID): Promise<null> {
    try {
      logger.info("Deleting user addresses");
      return await apiClient.delete(`/orders/addresses/${address_id}`);
    } catch (error) {
      logger.error("Failed to delete user address", { error });
      throw error;
    }
  }

  /**
   * Создание заказа из корзины
   */
  async createOrder(orderData: ICreateOrder): Promise<IOrder> {
    try {
      logger.info("Creating order", { orderData });
      return await apiClient.post<IOrder>("/orders", orderData);
    } catch (error) {
      logger.error("Failed to create order", { error });
      throw error;
    }
  }

  /**
   * Получение моих заказов
   */
  async getMyOrders() {
    try {
      logger.info("Fetching user orders");
      const response = await apiClient.get("/orders/my");
      return response;
    } catch (error) {
      logger.error("Failed to fetch orders", { error });
      throw error;
    }
  }

  /**
   * Получение деталей заказа
   */
  async getOrderDetails(orderId: string) {
    try {
      logger.info("Fetching order details", { orderId });
      return await apiClient.get(`/orders/my/${orderId}`);
    } catch (error) {
      logger.error("Failed to fetch order details", { error, orderId });
      throw error;
    }
  }

  /**
   * Отмена заказа
   */
  async cancelOrder(orderId: string): Promise<IOrder> {
    try {
      logger.info("Cancelling order", { orderId });
      return await apiClient.patch<IOrder>(`/orders/${orderId}/cancel`);
    } catch (error) {
      logger.error("Failed to cancel order", { orderId, error });
      throw error;
    }
  }

  /**
   * Получение списка пунктов выдачи
   */
  async getDeliveryPoints(): Promise<IUserDeliveryPoint[]> {
    try {
      logger.info("Fetching pickup points");
      return await apiClient.get(`/orders/delivery_points`);
    } catch (error) {
      logger.error("Failed to fetch pickup points", { error });
      throw error;
    }
  }

  async saveDeliveryPoint(pointData: IDeliveryPoint): Promise<IUserDeliveryPoint> {
    try {
      logger.info("Saving user delivery point", { pointData });
      return await apiClient.post<IUserDeliveryPoint>(`/orders/delivery_points`, pointData);
    } catch (error) {
      logger.error("Failed to save user delivery point", { error });
      throw error;
    }
  }

  async deleteDeliveryPoint(delivery_point_id: UUID): Promise<null> {
    try {
      logger.info("Deleting user delivery point");
      return await apiClient.delete(`/orders/delivery_points/${delivery_point_id}`);
    } catch (error) {
      logger.error("Failed to delete user delivery point", { error });
      throw error;
    }
  }

  /**
   * Получение доступных методов оплаты
   */
  async getPaymentMethods(): Promise<IPaymentMethod[]> {
    // Единственный метод оплаты - ЮKassa
    return [
      {
        id: PaymentMethod.ONLINE,
        name: "ЮKassa",
        icon: "/src/assets/images/yookassa-logo-black.svg",
        is_available: true,
      },
    ];
  }
}

export const orderService = new OrderService();
