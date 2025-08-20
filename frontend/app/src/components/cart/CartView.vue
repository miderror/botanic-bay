<script setup lang="ts">
/**
 * Компонент для отображения корзины покупок.
 * Позволяет просматривать товары, управлять их количеством,
 * применять промокоды и оформлять заказ.
 */
import CartQuantityControl from "@/components/cart/CartQuantityControl.vue";
import CheckoutModal from "@/components/checkout/CheckoutModal.vue";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import CloseButton from "@/components/icons/CloseButton.vue";
import OrdersIcon from "@/components/icons/OrdersIcon.vue";
import { useCart } from "@/composables/useCart";
import { useCartInitialization } from "@/composables/useCartInitialization";
import { useNotification } from "@/composables/useNotification";
import { useCartStore } from "@/stores/cart";
import { useProductQuantityStore } from "@/stores/productQuantityStore";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import { storeToRefs } from "pinia";
import { computed, onMounted, onUnmounted, ref } from "vue";

// Инициализация состояния корзины
const { isInitialized } = useCartInitialization();

// Подключаем необходимые composables
const { showNotification } = useNotification();
const productQuantityStore = useProductQuantityStore();

// Получаем store корзины и его состояние
const cartStore = useCartStore();
const { remainingTime } = storeToRefs(cartStore);

// Получаем методы работы с корзиной
const { cart, isLoading, error, initCart, removeFromCart, formatRemainingTime, isItemLoading } = useCart();

// UI состояние
const promoCode = ref("");
const promoError = ref("");
const showCheckoutModal = ref(false);

// Форматированное время для отображения
const formattedRemainingTime = computed(() => {
  return formatRemainingTime(remainingTime.value || 0);
});

const getImageUrl = (imageUrl: string | null) => {
  if (!imageUrl || imageUrl === "") return "/images/placeholder.jpg";
  if (imageUrl.startsWith("http") || imageUrl.startsWith("/media")) {
    return imageUrl;
  }
  return `/media/products/${imageUrl}`;
};

// Получение доступного количества товара
const getAvailableQuantity = (productId: string): number => {
  return productQuantityStore.getQuantity(productId) ?? 0;
};

// Открытие модального окна оформления заказа
const openCheckout = () => {
  try {
    if (!cart.value?.items.length) {
      showNotification("Корзина пуста", "error");
      return;
    }

    if (!remainingTime.value) {
      showNotification("Корзина неактивна", "error");
      return;
    }

    logger.info("Opening checkout modal", {
      cartId: cart.value.id,
      totalItems: cart.value.items.length,
      total: cart.value.total,
    });

    // Дополнительная проверка перед установкой состояния
    logger.debug("Setting showCheckoutModal to true");
    showCheckoutModal.value = true;
  } catch (error) {
    console.error("❌ Error in openCheckout", { error });
    showNotification("Произошла ошибка при открытии формы оплаты", "error");
  }
};

// Применение промокода
const applyPromoCode = () => {
  promoError.value = "Неверный промокод!";
  promoCode.value = "";

  logger.info("Attempt to apply promo code", {
    promoCode: promoCode.value,
  });
};

// Хуки жизненного цикла
onMounted(async () => {
  logger.debug("CartView mounted", {
    isInitialized: isInitialized.value,
    hasCart: !!cart.value,
    remainingTime: remainingTime.value,
  });

  // Инициализация корзины и таймера
  if (!cart.value) {
    await initCart();
  } else if (!(cartStore as { expirationTimer?: number }).expirationTimer && remainingTime.value) {
    logger.debug("Restarting timer in CartView", {
      remainingTime: remainingTime.value,
    });
    cartStore.startExpirationTimer();
  }
});

// Очистка при размонтировании
onUnmounted(() => {
  logger.debug("CartView unmounting", {
    remainingTime: remainingTime.value,
    hasCart: !!cart.value,
  });

  // Останавливаем отслеживание количества товаров
  if (cart.value?.items) {
    cart.value.items.forEach((item) => {
      productQuantityStore.stopPolling(item.product_id);
    });
  }
});
</script>

<template>
  <div class="cart-view">
    <!-- Добавляем фоновый паттерн -->
    <div class="cart-background"></div>

    <!-- Индикатор загрузки -->
    <LoadingSpinner v-if="isLoading" />

    <!-- Отображение ошибок -->
    <div
      v-else-if="error"
      class="error-message"
    >
      {{ error }}
    </div>

    <!-- Пустая корзина -->
    <div
      v-else-if="!cart?.items?.length"
      class="empty-cart"
    >
      <div class="empty-cart-icon">
        <OrdersIcon class="icon" />
      </div>
      <div class="empty-cart-text">Корзина пуста</div>
      <router-link
        to="/catalog"
        class="view-catalog-btn"
      >
        ПОСМОТРЕТЬ КАТАЛОГ
      </router-link>
    </div>

    <!-- Содержимое корзины -->
    <template v-else>
      <div class="cart-content">
        <!-- Таймер жизни корзины -->
        <div
          v-if="remainingTime"
          class="cart-timer"
        >
          Корзина будет доступна еще: {{ formattedRemainingTime }}
        </div>

        <!-- Ввод промокода -->
        <div
          class="promo-code"
          :class="{ error: promoError }"
        >
          <input
            v-model="promoCode"
            type="text"
            :placeholder="!promoError ? 'Введите промокод' : promoError"
            @input="promoError = ''"
            class="promo-input"
          />
          <button
            @click="applyPromoCode"
            class="promo-btn"
            :class="{ active: promoCode.length > 0 }"
          >
            ДОБАВИТЬ
          </button>
        </div>

        <!-- Список товаров в корзине -->
        <div class="cart-items">
          <div
            v-for="item in cart.items"
            :key="item.id"
            class="cart-item"
            :class="{ loading: isItemLoading(item.product_id) }"
          >
            <!-- Изображение товара -->
            <div class="item-image">
              <img
                :src="getImageUrl(item.image_url)"
                :alt="item.product_name"
              />
            </div>

            <!-- Информация о товаре -->
            <div class="item-info">
              <div class="item-name">{{ item.product_name }}</div>

              <!-- Используем единый компонент управления количеством -->
              <CartQuantityControl
                :product-id="item.product_id"
                :max-quantity="getAvailableQuantity(item.product_id)"
                :disabled="isItemLoading(item.product_id)"
                variant="cart"
              />

              <div class="item-price">{{ formatPrice(item.price) }}</div>
              <div class="item-stock">В наличии {{ getAvailableQuantity(item.product_id) }} шт.</div>
            </div>

            <!-- Кнопка удаления товара -->
            <button
              @click="removeFromCart(item.product_id)"
              class="delete-btn"
              :disabled="isItemLoading(item.product_id)"
              aria-label="Удалить товар"
            >
              <CloseButton />
            </button>
          </div>
        </div>
      </div>

      <!-- Кнопка оформления заказа -->
      <div class="cart-checkout">
        <button
          @click="openCheckout"
          class="checkout-btn"
          :disabled="!cart?.items?.length || !remainingTime"
        >
          ОПЛАТИТЬ {{ formatPrice(cart?.total || 0) }}
        </button>
      </div>

      <!-- Модальное окно оформления заказа -->
      <CheckoutModal
        v-if="showCheckoutModal"
        :isOpen="showCheckoutModal"
        @close="showCheckoutModal = false"
      />
    </template>
  </div>
</template>

<style>
@import "@/assets/styles/cart.css";
</style>
