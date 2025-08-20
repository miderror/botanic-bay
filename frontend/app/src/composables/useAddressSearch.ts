import { cdekService } from "@/services/cdekService";
import type { IAddressSearchParams, IAddressSearchResult } from "@/types/cdek";
import { logger } from "@/utils/logger";
import { readonly, ref } from "vue";

export interface LocationCoords {
  latitude: number;
  longitude: number;
}

export function useAddressSearch() {
  // Состояние
  const searchResults = ref<IAddressSearchResult[]>([]);
  const isSearching = ref(false);
  const searchError = ref<string | null>(null);

  // Переменная для хранения таймера дебаунса
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  /**
   * Поиск адресов для доставки с дебаунсингом
   */
  const searchDeliveryAddresses = async (query: string, userLocation?: LocationCoords) => {
    // Очищаем предыдущий таймер
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    // Если запрос слишком короткий, очищаем результаты
    if (query.length < 3) {
      searchResults.value = [];
      searchError.value = null;
      return;
    }

    // Устанавливаем новый таймер для дебаунса (300мс)
    debounceTimer = setTimeout(async () => {
      try {
        isSearching.value = true;
        searchError.value = null;

        const params: IAddressSearchParams = {
          query,
          limit: 5,
        };

        // Добавляем координаты пользователя если они есть
        if (userLocation) {
          params.user_latitude = userLocation.latitude;
          params.user_longitude = userLocation.longitude;
        }

        logger.info("Searching delivery addresses", { params });
        const results = await cdekService.searchDeliveryAddresses(params);

        searchResults.value = results;
        logger.info("Address search completed", { count: results.length });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to search addresses";
        searchError.value = message;
        logger.error("Address search failed", { query, error });
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
    searchDeliveryAddresses,
    clearResults,
    cancelSearch,
  };
}
