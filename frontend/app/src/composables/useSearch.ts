import { productService } from "@/services/productService";
import { logger } from "@/utils/logger";
import { computed, ref } from "vue";

// Создаем глобальное состояние вне composable
const globalSearchActive = ref(false);
const globalSearchQuery = ref("");

export function useSearch() {
  // Состояние загрузки и ошибок
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Вычисляемые свойства
  const isSearchActive = computed({
    get: () => globalSearchActive.value,
    set: (value: boolean) => {
      logger.debug("Search state changing", {
        from: globalSearchActive.value,
        to: value,
      });
      globalSearchActive.value = value;
    },
  });

  const searchQuery = computed({
    get: () => globalSearchQuery.value,
    set: (value: string) => {
      logger.debug("Search query changing", {
        from: globalSearchQuery.value,
        to: value,
      });
      globalSearchQuery.value = value;
    },
  });

  // Методы
  const setSearchActive = (active: boolean) => {
    isSearchActive.value = active;
  };

  const setSearchQuery = (query: string) => {
    searchQuery.value = query;
  };

  const resetSearch = () => {
    logger.debug("Resetting search state");
    isSearchActive.value = false;
    searchQuery.value = "";
  };

  /**
   * Выполняет поиск продуктов по запросу
   */
  const searchProducts = async (query: string) => {
    try {
      isLoading.value = true;
      error.value = null;
      setSearchQuery(query);

      logger.info("Searching products", { query });
      const response = await productService.searchProducts(query);

      return {
        items: response.items,
        total: response.total,
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to search products";
      error.value = message;
      logger.error("Search failed", { query, error: err });
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  return {
    // Состояние
    isSearchActive,
    searchQuery,
    isLoading,
    error,

    // Методы
    setSearchActive,
    setSearchQuery,
    resetSearch,
    searchProducts,
  };
}
