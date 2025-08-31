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
import { useCheckoutStore } from "@/stores/checkout";
import { promoCodeService } from "@/services/promoCodeService";
import { useImageUrl } from "@/composables/useImageUrl";

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

const checkoutStore = useCheckoutStore();
const { getImageUrl, handleImageError } = useImageUrl();

// UI состояние
const promoCodeInput = ref("");
const promoError = ref("");
const isApplyingPromo = ref(false);
const showCheckoutModal = ref(false);

// Форматированное время для отображения
const formattedRemainingTime = computed(() => {
  return formatRemainingTime(remainingTime.value || 0);
});

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


// Вычисляемое свойство для итоговой суммы с учетом скидки
const finalTotal = computed(() => {
  const total = cart.value?.total || 0;
  if (checkoutStore.discountPercent > 0) {
    const discount = (total * checkoutStore.discountPercent) / 100;
    return total - discount;
  }
  return total;
});

// Применение промокода
const applyPromoCode = async () => {
  if (!promoCodeInput.value.trim()) return;
  
  isApplyingPromo.value = true;
  promoError.value = "";

  try {
    const response = await promoCodeService.applyPromoCode(promoCodeInput.value);
    if (response.is_valid) {
      checkoutStore.setPromoCode(response.code, response.discount_percent);
      showNotification("Промокод применен!", "success");
      promoCodeInput.value = "";
    } else {
      promoError.value = response.message;
      checkoutStore.setPromoCode(null, 0); // Сбрасываем промокод в сторе
    }
  } catch (err) {
    promoError.value = "Ошибка при проверке промокода.";
    checkoutStore.setPromoCode(null, 0);
  } finally {
    isApplyingPromo.value = false;
  }
};

const removePromoCode = () => {
  checkoutStore.setPromoCode(null, 0);
  showNotification("Промокод удален", "info");
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
        <div class="promo-code" :class="{ error: promoError }">
          <input
            v-model="promoCodeInput"
            type="text"
            :placeholder="promoError ? promoError : 'Введите промокод'"
            @input="promoError = ''"
            class="promo-input"
            :disabled="!!checkoutStore.promoCode"
          />
          <button
            @click="applyPromoCode"
            class="promo-btn"
            :class="{ active: promoCodeInput.length > 0 && !checkoutStore.promoCode }"
            :disabled="isApplyingPromo || !!checkoutStore.promoCode"
          >
            {{ isApplyingPromo ? '...' : 'ДОБАВИТЬ' }}
          </button>
        </div>

        <!-- Отображение примененного промокода -->
        <div v-if="checkoutStore.promoCode" class="applied-promo">
          <span>Промокод "{{ checkoutStore.promoCode }}" применен. Скидка {{ checkoutStore.discountPercent }}%</span>
          <button @click="removePromoCode" class="remove-promo-btn">✕</button>
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
                @error="handleImageError" 
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
          ОПЛАТИТЬ {{ formatPrice(finalTotal) }}
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
