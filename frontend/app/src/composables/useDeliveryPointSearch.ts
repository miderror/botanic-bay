import { ref, readonly } from "vue";
import { logger } from "@/utils/logger";
import { cdekService } from "@/services/cdekService";
import type { IDeliveryPointSearchResult, IDeliveryPointSearchParams } from "@/types/cdek";

export interface LocationCoords {
  latitude: number;
  longitude: number;
}

export function useDeliveryPointSearch() {
  // Состояние
  const searchResults = ref<IDeliveryPointSearchResult[]>([]);
  const isSearching = ref(false);
  const searchError = ref<string | null>(null);

  // Переменная для хранения таймера дебаунса
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  /**
   * Поиск ПВЗ по адресу пользователя с дебаунсингом
   */
  const searchDeliveryPoints = async (addressQuery: string, userLocation?: LocationCoords) => {
    // Очищаем предыдущий таймер
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    // Если запрос слишком короткий, очищаем результаты
    if (addressQuery.length < 3) {
      searchResults.value = [];
      searchError.value = null;
      return;
    }

    // Устанавливаем новый таймер для дебаунса (300мс)
    debounceTimer = setTimeout(async () => {
      try {
        isSearching.value = true;
        searchError.value = null;

        const params: IDeliveryPointSearchParams = {
          address_query: addressQuery,
          limit: 20,
        };

        // Добавляем координаты пользователя если они есть
        if (userLocation) {
          params.user_latitude = userLocation.latitude;
          params.user_longitude = userLocation.longitude;
        }

        logger.info("Searching delivery points by address", { params });
        const results = await cdekService.searchDeliveryPointsByAddress(params);

        searchResults.value = results;
        logger.info("Delivery points search completed", { count: results.length });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to search delivery points";
        searchError.value = message;
        logger.error("Delivery points search failed", { addressQuery, error });
        searchResults.value = [];
      } finally {
        isSearching.value = false;
      }
    }, 300);
  };

  /**
   * Очистка результатов поиска
   */
  const clearResults = () => {
    searchResults.value = [];
    searchError.value = null;
    isSearching.value = false;

    // Очищаем таймер если он есть
    if (debounceTimer) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }
  };

  /**
   * Отмена текущего поиска
   */
  const cancelSearch = () => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }
    isSearching.value = false;
  };

  return {
    // Состояние (readonly для предотвращения изменений извне)
    searchResults: readonly(searchResults),
    isSearching: readonly(isSearching),
    searchError: readonly(searchError),

    // Методы
    searchDeliveryPoints,
    clearResults,
    cancelSearch,
  };
}
