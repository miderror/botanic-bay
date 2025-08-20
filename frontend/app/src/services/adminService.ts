import type {
  ExportFormat,
  IAdminOrderFilter,
  IAdminOrderList,
  IAdminPayoutFilter,
  IAdminPayoutList,
  IAdminProduct,
  IAdminProductFilter,
  IAdminUser,
  IAdminUserFilter,
  IExportOrdersRequest,
  IOrderStats,
  IPaginatedResponse,
} from "@/types/admin";
import { type IReferralPayoutRequest, ReferralPayoutStatus } from "@/types/business.ts";
import type { IOrder } from "@/types/order";
import { logger } from "@/utils/logger";
import { apiClient } from "./httpClient";

/**
 * Сервис для работы с админским API
 * Реализует паттерн репозитория для работы с данными
 */
class AdminService {
  private baseUrl: string;

  constructor(baseUrl: string = "/api/v1/admin") {
    this.baseUrl = baseUrl;
  }

  private async request(url: string, options: RequestInit = {}) {
    // Получаем Telegram WebApp данные
    const webAppData = window.Telegram?.WebApp?.initData;
    const userData = window.Telegram?.WebApp?.initDataUnsafe?.user;

    // Добавляем заголовки
    const headers = {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": webAppData || "",
      "X-Telegram-User-Id": userData?.id?.toString() || "",
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Получение списка всех категорий товаров
   */

  async getCategories(): Promise<string[]> {
    return apiClient.get("/admin/products/categories");
  }

  async createProduct(data: Omit<IAdminProduct, "id">): Promise<IAdminProduct> {
    logger.info("Creating new product", { productData: data });
    return apiClient.post("/admin/products", data);
  }
  /**
   * Получение списка товаров с фильтрацией и пагинацией
   */

  async getProducts(
    page: number = 1,
    limit: number = 50,
    filters?: IAdminProductFilter,
  ): Promise<IPaginatedResponse<IAdminProduct>> {
    const params = {
      skip: (page - 1) * limit,
      limit,
      ...filters,
    };

    logger.info("Fetching admin products", {
      page,
      limit,
      filters,
    });

    return apiClient.get("/admin/products", params);
  }

  async updateProduct(id: string, data: Partial<IAdminProduct>): Promise<IAdminProduct> {
    logger.info("Updating product with image:", {
      productId: id,
      image_url: data.image_url,
      background_image_url: data.background_image_url,
    });
    return apiClient.patch(`/admin/products/${id}`, data);
  }

  async deleteProduct(id: string): Promise<void> {
    return apiClient.delete(`/admin/products/${id}`);
  }

  // Добавим метод для загрузки изображений
  async uploadProductImage(file: File): Promise<{ image_url: string }> {
    const result = await apiClient.uploadFile("/admin/products/upload-image", file);
    logger.info("Image uploaded:", { result });
    return result;
  }

  /**
   * Получение списка пользователей
   */

  async getUsers(
    page: number = 1,
    limit: number = 50,
    filters?: IAdminUserFilter,
  ): Promise<IPaginatedResponse<IAdminUser>> {
    const skip = (page - 1) * limit;

    return apiClient.get("/admin/users", {
      skip, // Добавляем параметр skip вместо page
      limit,
      ...filters,
    });
  }

  async updateUserRoles(userId: string, roles: string[]): Promise<IAdminUser> {
    const VALID_ROLES = ["user", "admin", "manager", "support"];

    // Проверяем, что все роли валидны
    const invalidRoles = roles.filter((role) => !VALID_ROLES.includes(role));

    if (invalidRoles.length > 0) {
      logger.error("Invalid roles detected", { invalidRoles });
      throw new Error(`Некорректные роли: ${invalidRoles.join(", ")}`);
    }

    try {
      const result = await apiClient.patch(`/admin/users/${userId}/roles`, { roles });

      logger.info("User roles updated successfully", {
        userId,
        roles,
      });

      return result;
    } catch (error) {
      logger.error("Failed to update user roles", {
        userId,
        roles,
        error,
      });
      throw error;
    }
  }

  async toggleUserBlock(userId: string): Promise<IAdminUser> {
    return apiClient.patch(`/admin/users/${userId}/block`);
  }

  /**
   * Получение списка заказов для админки
   */
  async getOrders(
    page: number = 1,
    limit: number = 50,
    filters?: IAdminOrderFilter,
  ): Promise<IAdminOrderList> {
    try {
      const skip = (page - 1) * limit;

      logger.info("Fetching orders for admin", {
        page,
        limit,
        filters,
      });

      // Преобразуем фильтры в параметры запроса
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const params: Record<string, any> = {
        skip,
        limit,
      };

      // Добавляем фильтры, если они есть
      if (filters) {
        if (filters.order_id) params.order_id = filters.order_id;
        if (filters.status) params.status = filters.status;
        if (filters.from_date) params.from_date = filters.from_date;
        if (filters.to_date) params.to_date = filters.to_date;
        if (filters.min_total !== undefined) params.min_total = filters.min_total;
        if (filters.max_total !== undefined) params.max_total = filters.max_total;
      }

      return await apiClient.get("/admin/orders", params);
    } catch (error) {
      logger.error("Failed to fetch orders", { error });
      throw error;
    }
  }

  /**
   * Обновление статуса заказа
   */
  async updateOrderStatus(orderId: string, status: string, comment?: string): Promise<IOrder> {
    try {
      logger.info("Updating order status", {
        orderId,
        status,
        comment,
      });

      return await apiClient.patch(`/admin/orders/${orderId}/status`, {
        status,
        comment,
      });
    } catch (error) {
      logger.error("Failed to update order status", {
        orderId,
        status,
        error,
      });
      throw error;
    }
  }

  /**
   * Получение деталей заказа
   */
  async getOrderDetails(orderId: string): Promise<IOrder> {
    try {
      logger.info("Fetching order details", { orderId });

      return await apiClient.get(`/admin/orders/${orderId}`);
    } catch (error) {
      logger.error("Failed to fetch order details", {
        orderId,
        error,
      });
      throw error;
    }
  }

  /**
   * Получение статистики заказов
   */
  async getOrderStats(): Promise<IOrderStats> {
    try {
      logger.info("Fetching order statistics");
      return await apiClient.get("/admin/orders/stats");
    } catch (error) {
      logger.error("Failed to fetch order statistics", { error });
      throw error;
    }
  }

  // Добавить метод для экспорта
  async exportOrders(format: ExportFormat, filters?: IAdminOrderFilter): Promise<Blob> {
    try {
      logger.info("Exporting orders", { format, filters });

      // Создаем запрос
      const requestData: IExportOrdersRequest = {
        format,
        filters,
      };

      // Выполняем запрос с опцией responseType: 'blob'
      const response = await apiClient.post("/admin/orders/export", requestData, {
        responseType: "blob",
      });

      return response;
    } catch (error) {
      logger.error("Failed to export orders", { error, format, filters });
      throw error;
    }
  }

  /**
   * Экспорт заказов через Telegram бота
   * @param format Формат экспорта (CSV/Excel)
   * @param filters Фильтры для выборки заказов
   * @returns Promise с результатом операции
   */
  async exportOrdersToTelegram(
    format: ExportFormat,
    filters?: IAdminOrderFilter,
  ): Promise<{ success: boolean; message: string }> {
    try {
      logger.info("Exporting orders via Telegram bot", { format, filters });

      // Получаем telegram_user_id из Telegram WebApp
      const telegramUserId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id;

      if (!telegramUserId) {
        throw new Error("Telegram user ID not available");
      }

      // Выполняем запрос на экспорт, передавая telegram_user_id как query параметр
      const response = await apiClient.post(
        `/admin/orders/export-to-telegram?telegram_user_id=${telegramUserId}`,
        {
          format,
          filters,
        },
      );

      return response;
    } catch (error) {
      logger.error("Failed to export orders via Telegram", { error, format, filters });
      throw error;
    }
  }

  async getPayoutRequests(
    page: number = 1,
    page_size: number = 50,
    filters?: IAdminPayoutFilter,
  ): Promise<IAdminPayoutList> {
    try {
      logger.info("Fetching payout requests for admin", {
        page,
        page_size,
        filters,
      });

      // Преобразуем фильтры в параметры запроса
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const params: Record<string, any> = {
        page,
        page_size,
      };

      // Добавляем фильтры, если они есть
      if (filters) {
        if (filters.id) params.id = filters.id;
        if (filters.status) params.status = filters.status;
        if (filters.fromDate) params.from_date = filters.fromDate;
        if (filters.toDate) params.to_date = filters.toDate;
      }
      console.log(params);

      return await apiClient.get("/admin/payout-request", params);
    } catch (error) {
      logger.error("Failed to fetch payout requests", { error });
      throw error;
    }
  }

  async updatePayoutStatus(id: string, status: ReferralPayoutStatus): Promise<IReferralPayoutRequest> {
    try {
      logger.info("Updating payout request status", {
        id,
        status,
      });

      const action = status == ReferralPayoutStatus.APPROVED ? "approve" : "reject";
      return await apiClient.post(`/admin/payout-request/${id}/${action}`);
    } catch (error) {
      logger.error("Failed to update request status", {
        orderId,
        status,
        error,
      });
      throw error;
    }
  }
}

// Создаем и экспортируем экземпляр сервиса
export const adminService = new AdminService();
