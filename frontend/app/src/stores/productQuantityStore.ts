import config from "@/config";
import { productService } from "@/services/productService";
import { logger } from "@/utils/logger";
import { defineStore } from "pinia";
import { ref } from "vue";

interface QuantityMap {
  [productId: string]: {
    quantity: number;
    lastUpdated: number;
    pollTimer?: number;
  };
}

export const useProductQuantityStore = defineStore("productQuantity", () => {
  // Состояние
  const quantities = ref<QuantityMap>({});
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Получение количества для продукта
  const getQuantity = (productId: string) => {
    return quantities.value[productId]?.quantity ?? null;
  };

  // Обновление количества для продукта
  const fetchQuantity = async (productId: string) => {
    if (!config.polling.enabled || !config.polling.productQuantity) {
      return;
    }

    try {
      isLoading.value = true;
      error.value = null;

      const quantity = await productService.getAvailableQuantity(productId);

      quantities.value[productId] = {
        quantity,
        lastUpdated: Date.now(),
        pollTimer: quantities.value[productId]?.pollTimer,
      };

      // logger.debug('Product quantity updated', {
      //   productId,
      //   quantity,
      //   timestamp: new Date().toISOString()
      // })
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Failed to fetch quantity";
      logger.error("Failed to fetch product quantity", {
        productId,
        error: err,
      });
    } finally {
      isLoading.value = false;
    }
  };

  // Запуск поллинга для продукта
  const startPolling = (productId: string, interval?: number) => {
    if (!config.polling.enabled || !config.polling.productQuantity) {
      return;
    }

    // Остановим существующий поллинг если есть
    stopPolling(productId);

    // Получим начальные данные
    fetchQuantity(productId);

    // Запустим новый поллинг
    const timer = window.setInterval(() => fetchQuantity(productId), interval || config.polling.interval);

    quantities.value[productId] = {
      ...quantities.value[productId],
      pollTimer: timer,
    };

    // logger.debug('Started quantity polling', {
    //   productId,
    //   interval: interval || config.polling.interval
    // })
  };

  // Остановка поллинга для продукта
  const stopPolling = (productId: string) => {
    const timer = quantities.value[productId]?.pollTimer;
    if (timer) {
      clearInterval(timer);
      quantities.value[productId] = {
        ...quantities.value[productId],
        pollTimer: undefined,
      };
      logger.debug("Stopped quantity polling", { productId });
    }
  };

  // Очистка всех таймеров
  const cleanup = () => {
    Object.keys(quantities.value).forEach((productId) => {
      stopPolling(productId);
    });
    quantities.value = {};
  };

  return {
    // Состояние
    quantities,
    isLoading,
    error,

    // Методы
    getQuantity,
    fetchQuantity,
    startPolling,
    stopPolling,
    cleanup,
  };
});
