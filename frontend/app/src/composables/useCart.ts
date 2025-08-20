import { useNotification } from "@/composables/useNotification";
import { useCartStore } from "@/stores/cart";
import { logger } from "@/utils/logger";
import { storeToRefs } from "pinia";
import { computed, onUnmounted } from "vue";

export function useCart() {
  const cartStore = useCartStore();
  const { showNotification } = useNotification();

  // Получаем реактивные ссылки на состояние стора
  const { cart, isLoading, error, remainingTime } = storeToRefs(cartStore);

  // Проверяем состояние таймера при каждой инициализации
  const checkTimer = () => {
    // Проверяем наличие таймера через внутреннее состояние стора
    const hasActiveTimer = (cartStore as { _timer?: number })._timer || false;

    if (remainingTime.value && !hasActiveTimer) {
      // logger.debug('Timer not running, starting in useCart', {
      //   remainingTime: remainingTime.value,
      //   hasTimer: hasActiveTimer
      // })
      try {
        cartStore.startExpirationTimer();
      } catch (err) {
        logger.error("Failed to start timer", {
          error: err,
          remainingTime: remainingTime.value,
        });
      }
    }
  };

  // Запускаем проверку при инициализации
  checkTimer();

  // logger.debug('useCart initialized', {
  //   hasRemainingTime: remainingTime.value !== null,
  //   remainingTimeValue: remainingTime.value,
  //   hasTimer: !!(cartStore as any).expirationTimer
  // })

  // Вычисляемые свойства из стора
  const itemsCount = computed(() => cartStore.itemsCount);
  const totalPrice = computed(() => cartStore.totalPrice);

  // Форматирование оставшегося времени
  const formatRemainingTime = (ms: number): string => {
    // logger.debug('Formatting remaining time', { ms })
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    const formatted = `${minutes}:${seconds.toString().padStart(2, "0")}`;
    // logger.debug('Formatted time', { minutes, seconds, formatted })
    return formatted;
  };

  // Методы для работы с корзиной
  const addToCart = async (productId: string, quantity: number) => {
    try {
      await cartStore.addToCart(productId, quantity);
      showNotification("Товар добавлен в корзину", "success");
      checkTimer(); // Проверяем таймер после изменения корзины
    } catch (err) {
      showNotification("Не удалось добавить товар в корзину", "error");
      logger.error("Failed to add to cart", {
        productId,
        quantity,
        error: err,
      });
    }
  };

  const updateQuantity = async (productId: string, quantity: number) => {
    try {
      await cartStore.updateQuantity(productId, quantity);
      showNotification("Количество товара обновлено", "success");
      checkTimer(); // Проверяем таймер после изменения корзины
    } catch (err) {
      showNotification("Не удалось обновить количество товара", "error");
      logger.error("Failed to update quantity", {
        productId,
        quantity,
        error: err,
      });
    }
  };

  const removeFromCart = async (productId: string) => {
    try {
      await cartStore.removeFromCart(productId);

      // Показываем уведомление об успешном удалении
      if (cartStore.itemsCount === 0) {
        showNotification("Корзина очищена", "success");
      } else {
        showNotification("Товар удален из корзины", "success");
      }
      checkTimer(); // Проверяем таймер после изменения корзины
    } catch (err) {
      logger.error("Failed to remove from cart", {
        productId,
        error: err,
      });
      showNotification("Не удалось удалить товар из корзины", "error");
    }
  };

  const clearCart = async () => {
    try {
      await cartStore.clearCart();
      showNotification("Корзина очищена", "success");
      checkTimer(); // Проверяем таймер после очистки корзины
    } catch (err) {
      showNotification("Не удалось очистить корзину", "error");
      logger.error("Failed to clear cart", { error: err });
    }
  };

  // Инициализация корзины при монтировании
  const initCart = async () => {
    try {
      await cartStore.fetchCart();
      checkTimer(); // Проверяем таймер после инициализации корзины
    } catch (err) {
      showNotification("Не удалось загрузить корзину", "error");
      logger.error("Failed to init cart", { error: err });
    }
  };

  // Очистка при размонтировании
  onUnmounted(() => {
    logger.debug("useCart unmounting", {
      hasTimer: !!(cartStore as { expirationTimer?: number }).expirationTimer,
      remainingTime: remainingTime.value,
    });
    cartStore.cleanup();
  });

  return {
    // Состояние
    cart,
    isLoading,
    error,
    remainingTime,

    // Вычисляемые свойства
    itemsCount,
    totalPrice,

    // Методы
    initCart,
    addToCart,
    updateQuantity,
    removeFromCart,
    clearCart,
    formatRemainingTime,
    isItemLoading: cartStore.isItemLoading,
    checkTimer, // Экспортируем метод проверки таймера
  };
}
