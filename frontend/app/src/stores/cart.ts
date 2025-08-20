// Стор для управления корзиной покупок
import { apiClient } from "@/services/httpClient";
import { useProductQuantityStore } from "@/stores/productQuantityStore";
import type { ICart, ICartItem, ICartResponse } from "@/types/cart";
import { logger } from "@/utils/logger";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

// Вспомогательная функция для сортировки элементов корзины по ID товара
const sortCartItems = (items: ICartItem[]): ICartItem[] => {
  return [...items].sort((a, b) => a.product_id.localeCompare(b.product_id));
};

export const useCartStore = defineStore("cart", () => {
  // Подключаем стор для работы с количеством товаров
  const productQuantityStore = useProductQuantityStore();

  // Основное состояние корзины
  const cart = ref<ICart | null>(null); // Данные корзины
  const isLoading = ref(false); // Флаг загрузки
  const error = ref<string | null>(null); // Ошибки
  const remainingTime = ref<number | null>(null); // Оставшееся время жизни корзины

  // Set для хранения ID товаров, которые в процессе обновления
  const loadingItems = ref<Set<string>>(new Set());

  // Методы для управления состоянием загрузки отдельных товаров
  const setItemLoading = (productId: string) => {
    loadingItems.value.add(productId);
  };

  const unsetItemLoading = (productId: string) => {
    loadingItems.value.delete(productId);
  };

  const isItemLoading = (productId: string) => {
    return loadingItems.value.has(productId);
  };

  // Вычисляемые свойства
  const itemsCount = computed(() => {
    if (!cart.value?.items) return 0;
    return cart.value.items.reduce((acc, item) => acc + item.quantity, 0);
  });

  const totalPrice = computed(() => {
    if (!cart.value?.items) return 0;
    return cart.value.items.reduce((acc, item) => acc + item.price * item.quantity, 0);
  });

  // Управление таймером жизни корзины
  let expirationTimer: number | null = null;

  // Обновление времени жизни корзины
  const updateExpirationTime = (expiresAt: string | null) => {
    if (!expiresAt) {
      logger.debug("No expiration time received from API");
      remainingTime.value = null;
      stopExpirationTimer();
      return;
    }

    const expirationTimestamp = new Date(expiresAt).getTime();
    const now = new Date().getTime();
    const newRemainingTime = Math.max(0, expirationTimestamp - now);

    logger.debug("Updating expiration time from API", {
      expiresAt,
      expirationTimestamp,
      now,
      newRemainingTime,
      oldRemainingTime: remainingTime.value,
    });

    remainingTime.value = newRemainingTime;

    if (newRemainingTime === 0) {
      logger.info("Cart expired based on API time");
      clearCart();
      return;
    }

    startExpirationTimer();
  };

  // Запуск таймера обратного отсчета
  const startExpirationTimer = () => {
    stopExpirationTimer();

    if (!remainingTime.value) {
      // logger.debug('No remaining time, skipping timer start')
      return;
    }

    expirationTimer = window.setInterval(() => {
      if (remainingTime.value !== null) {
        remainingTime.value = Math.max(0, remainingTime.value - 1000);

        if (remainingTime.value === 0) {
          logger.info("Cart expired locally, clearing");
          clearCart();
          stopExpirationTimer();
        }
      }
    }, 1000);
  };

  // Остановка таймера
  const stopExpirationTimer = () => {
    if (expirationTimer) {
      // logger.debug('Stopping expiration timer', {
      //   currentRemainingTime: remainingTime.value
      // })
      clearInterval(expirationTimer);
      expirationTimer = null;
    }
  };

  // Получение актуальных данных корзины с сервера
  const fetchCart = async () => {
    try {
      isLoading.value = true;
      error.value = null;

      const response = await apiClient.get("/cart/my");

      // Обновляем данные корзины с сортировкой элементов
      cart.value = {
        ...response.cart,
        items: sortCartItems(response.cart.items),
      };

      // Обновляем время жизни корзины
      updateExpirationTime(cart.value?.expires_at || null);

      logger.info("Cart fetched successfully", {
        cartId: cart.value?.id,
        itemsCount: cart.value?.items.length,
        expiresAt: cart.value?.expires_at,
      });

      // Получаем актуальные данные о количестве для каждого товара
      if (cart.value?.items) {
        await Promise.all(
          cart.value.items.map((item) => productQuantityStore.fetchQuantity(item.product_id)),
        );
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch cart";
      error.value = message;
      logger.error("Failed to fetch cart", { error: err });
    } finally {
      isLoading.value = false;
    }
  };

  // Добавление товара в корзину
  const addToCart = async (productId: string, quantity: number) => {
    try {
      setItemLoading(productId);
      error.value = null;

      const response = await apiClient.post("/cart/add", {
        product_id: productId,
        quantity,
      });

      // Обновляем данные корзины с сортировкой элементов
      cart.value = {
        ...response.cart,
        items: sortCartItems(response.cart.items),
      };

      updateExpirationTime(response.cart?.expires_at || null);

      await productQuantityStore.fetchQuantity(productId);

      logger.info("Product added to cart and quantity updated", {
        productId,
        quantity,
        cartId: cart.value?.id,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to add product to cart";
      error.value = message;
      logger.error("Failed to add to cart", {
        error: err,
        productId,
        quantity,
      });

      await productQuantityStore.fetchQuantity(productId);

      throw err;
    } finally {
      unsetItemLoading(productId);
    }
  };

  // Обновление количества товара в корзине
  const updateQuantity = async (productId: string, quantity: number) => {
    try {
      setItemLoading(productId);
      error.value = null;

      const response = await apiClient.patch(`/cart/${productId}`, {
        quantity,
      });

      // Обновляем данные корзины с сортировкой элементов
      cart.value = {
        ...response.cart,
        items: sortCartItems(response.cart.items),
      };

      updateExpirationTime(response.cart?.expires_at || null);

      await productQuantityStore.fetchQuantity(productId);

      logger.info("Cart item quantity updated and stock refreshed", {
        productId,
        quantity,
        cartId: cart.value?.id,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to update quantity";
      error.value = message;
      logger.error("Failed to update quantity", {
        error: err,
        productId,
        quantity,
      });

      await productQuantityStore.fetchQuantity(productId);

      throw err;
    } finally {
      unsetItemLoading(productId);
    }
  };

  // Удаление товара из корзины
  const removeFromCart = async (productId: string) => {
    try {
      setItemLoading(productId);
      error.value = null;

      const response = await apiClient.delete<ICartResponse>(`/cart/${productId}`);

      if (!response?.cart) {
        // Если корзина пуста
        cart.value = {
          id: "",
          items: [],
          total: 0,
          expires_at: null,
          is_active: true,
        };
        updateExpirationTime(null);
      } else {
        // Обновляем данные корзины с сортировкой элементов
        cart.value = {
          ...response.cart,
          items: sortCartItems(response.cart.items),
        };
        updateExpirationTime(response.cart?.expires_at || null);
      }

      await productQuantityStore.fetchQuantity(productId);

      logger.info("Product removed from cart", {
        productId,
        cartId: cart.value?.id,
        itemsCount: cart.value?.items.length,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to remove product";
      error.value = message;
      logger.error("Failed to remove from cart", {
        error: err,
        productId,
      });

      await productQuantityStore.fetchQuantity(productId);

      throw err;
    } finally {
      unsetItemLoading(productId);
    }
  };

  // Очистка корзины
  const clearCart = async () => {
    try {
      isLoading.value = true;
      error.value = null;

      const productIds = cart.value?.items.map((item) => item.product_id) || [];

      try {
        // Пробуем отправить запрос на очистку
        await apiClient.delete("/cart");
      } catch (deleteErr) {
        logger.error("HTTP request to clear cart failed", { error: deleteErr });
        // Даже если HTTP-запрос не удался, продолжаем очистку локального состояния
      }

      // Очищаем локальное состояние независимо от результата HTTP-запроса
      cart.value = {
        id: "",
        items: [],
        total: 0,
        expires_at: null,
        is_active: true,
      };
      updateExpirationTime(null);

      try {
        // Обновляем доступные количества товаров
        await Promise.all(productIds.map((productId) => productQuantityStore.fetchQuantity(productId)));
      } catch (quantityErr) {
        logger.error("Failed to update quantities after cart clear", { error: quantityErr });
        // Не прерываем выполнение из-за ошибки обновления количеств
      }

      logger.info("Cart cleared");
      return { success: true };
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Failed to clear cart";
      logger.error("Failed to clear cart completely", { error: err });
      // Возвращаем объект вместо выброса исключения
      return { success: false, error: error.value };
    } finally {
      isLoading.value = false;
    }
  };

  // Очистка при размонтировании компонента
  const cleanup = () => {
    logger.debug("Cleaning up cart store", {
      hasTimer: !!expirationTimer,
      remainingTime: remainingTime.value,
    });
    stopExpirationTimer();
  };

  return {
    // Состояние
    cart,
    isLoading,
    error,
    remainingTime,

    // Геттеры
    itemsCount,
    totalPrice,

    // Методы
    fetchCart,
    addToCart,
    updateQuantity,
    removeFromCart,
    clearCart,
    cleanup,
    isItemLoading,
    startExpirationTimer,
    updateExpirationTime,
  };
});
