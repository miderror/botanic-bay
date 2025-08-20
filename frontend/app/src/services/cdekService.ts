import type {
  IAddress,
  IAddressSearchParams,
  IAddressSearchResult,
  IDeliveryPoint,
  IDeliveryPointSearchParams,
  IDeliveryPointSearchResult,
} from "@/types/cdek.ts";
import { logger } from "@/utils/logger";
import { apiClient } from "./httpClient";

export class CDEKService {
  /**
   * Получение точек ПВЗ/постаматов для отображения их на карте
   */
  async getDeliveryPoints(center: string) {
    try {
      logger.info("Fetching CDEK pickup points");
      return await apiClient.get<IDeliveryPoint[]>(
        `/cdek/delivery_points?center=${encodeURIComponent(center)}`,
      );
    } catch (error) {
      logger.error("Failed to fetch pickup points", { error });
      throw error;
    }
  }

  async getAddress(point: string) {
    try {
      logger.info("Fetching address for the point");
      return await apiClient.get<IAddress>(`/cdek/address?point=${encodeURIComponent(point)}`);
    } catch (error) {
      logger.error("Failed to fetch address", { error });
      throw error;
    }
  }

  /**
   * Поиск адресов для доставки по текстовому запросу
   */
  async searchDeliveryAddresses(params: IAddressSearchParams): Promise<IAddressSearchResult[]> {
    try {
      logger.info("Searching delivery addresses", { params });
      const searchParams = new URLSearchParams();

      searchParams.append("query", params.query);
      if (params.user_latitude !== undefined) {
        searchParams.append("user_latitude", params.user_latitude.toString());
      }
      if (params.user_longitude !== undefined) {
        searchParams.append("user_longitude", params.user_longitude.toString());
      }
      if (params.limit !== undefined) {
        searchParams.append("limit", params.limit.toString());
      }

      return await apiClient.get<IAddressSearchResult[]>(`/cdek/search/addresses?${searchParams}`);
    } catch (error) {
      logger.error("Failed to search delivery addresses", { error, params });
      throw error;
    }
  }

  /**
   * Поиск ПВЗ по адресу пользователя
   */
  async searchDeliveryPointsByAddress(
    params: IDeliveryPointSearchParams,
  ): Promise<IDeliveryPointSearchResult[]> {
    try {
      logger.info("Searching delivery points by address", { params });
      const searchParams = new URLSearchParams();

      searchParams.append("address_query", params.address_query);
      if (params.user_latitude !== undefined) {
        searchParams.append("user_latitude", params.user_latitude.toString());
      }
      if (params.user_longitude !== undefined) {
        searchParams.append("user_longitude", params.user_longitude.toString());
      }
      if (params.limit !== undefined) {
        searchParams.append("limit", params.limit.toString());
      }

      return await apiClient.get<IDeliveryPointSearchResult[]>(
        `/cdek/search/delivery-points?${searchParams}`,
      );
    } catch (error) {
      logger.error("Failed to search delivery points by address", { error, params });
      throw error;
    }
  }
}

// Создаем и экспортируем экземпляр сервиса
export const cdekService = new CDEKService();
