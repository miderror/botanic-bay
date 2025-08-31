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
import { useImageUrl } from "@/composables/useImageUrl";
import { useNotification } from "@/composables/useNotification";
import { useCartStore } from "@/stores/cart";
import { useCheckoutStore } from "@/stores/checkout";
import { useProductQuantityStore } from "@/stores/productQuantityStore";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import { storeToRefs } from "pinia";
import { computed, onMounted, onUnmounted, ref } from "vue";

const { isInitialized } = useCartInitialization();

const { showNotification } = useNotification();
const productQuantityStore = useProductQuantityStore();

const cartStore = useCartStore();
const { remainingTime } = storeToRefs(cartStore);

const { cart, isLoading, error, initCart, removeFromCart, formatRemainingTime, isItemLoading } = useCart();

const checkoutStore = useCheckoutStore();
const { getImageUrl, handleImageError } = useImageUrl();
const { promoCode, discountPercent, promoCodeStatus, promoCodeMessage } = storeToRefs(checkoutStore);

const promoCodeInput = ref("");
const showCheckoutModal = ref(false);

const onPromoInput = (event: Event) => {
  promoCodeInput.value = (event.target as HTMLInputElement).value;
};

const formattedRemainingTime = computed(() => {
  return formatRemainingTime(remainingTime.value || 0);
});

const getAvailableQuantity = (productId: string): number => {
  return productQuantityStore.getQuantity(productId) ?? 0;
};

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

    logger.debug("Setting showCheckoutModal to true");
    showCheckoutModal.value = true;
  } catch (error) {
    console.error("❌ Error in openCheckout", { error });
    showNotification("Произошла ошибка при открытии формы оплаты", "error");
  }
};

const finalTotal = computed(() => {
  const total = cart.value?.total || 0;
  if (discountPercent.value > 0) {
    const discount = (total * discountPercent.value) / 100;
    return total - discount;
  }
  return total;
});

const handleApplyPromoCode = () => {
  checkoutStore.applyPromoCode(promoCodeInput.value);
};

const handleRemovePromoCode = () => {
  checkoutStore.removePromoCode();
};

onMounted(async () => {
  logger.debug("CartView mounted", {
    isInitialized: isInitialized.value,
    hasCart: !!cart.value,
    remainingTime: remainingTime.value,
  });

  if (!cart.value) {
    await initCart();
  } else if (!(cartStore as { expirationTimer?: number }).expirationTimer && remainingTime.value) {
    logger.debug("Restarting timer in CartView", {
      remainingTime: remainingTime.value,
    });
    cartStore.startExpirationTimer();
  }
});

onUnmounted(() => {
  logger.debug("CartView unmounting", {
    remainingTime: remainingTime.value,
    hasCart: !!cart.value,
  });

  if (cart.value?.items) {
    cart.value.items.forEach((item) => {
      productQuantityStore.stopPolling(item.product_id);
    });
  }
});
</script>

<template>
  <div class="cart-view">
    <div class="cart-background"></div>
    <LoadingSpinner v-if="isLoading" />
    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>
    <div v-else-if="!cart?.items?.length" class="empty-cart">
      <div class="empty-cart-icon">
        <OrdersIcon class="icon" />
      </div>
      <div class="empty-cart-text">Корзина пуста</div>
      <router-link to="/catalog" class="view-catalog-btn"> ПОСМОТРЕТЬ КАТАЛОГ </router-link>
    </div>
    <template v-else>
      <div class="cart-content">
        <div v-if="remainingTime" class="cart-timer">
          Корзина будет доступна еще: {{ formattedRemainingTime }}
        </div>

        <div
          class="promo-code"
          :class="{
            success: promoCodeStatus === 'success',
            error: promoCodeStatus === 'error',
          }"
        >
          <div class="promo-content">
            <div v-if="promoCodeStatus === 'success' || promoCodeStatus === 'error'" class="promo-message">
              {{ promoCodeMessage }}
            </div>
            <input
              v-else
              :value="promoCodeInput"
              @input="onPromoInput"
              type="text"
              placeholder="Введите промокод"
              class="promo-input"
              :disabled="promoCodeStatus === 'loading'"
            />
          </div>

          <button
            v-if="promoCodeStatus !== 'success'"
            @click="handleApplyPromoCode"
            class="promo-btn"
            :class="{ active: promoCodeInput.length > 0 && promoCodeStatus !== 'error' }"
            :disabled="promoCodeStatus === 'loading' || !promoCodeInput.trim() || promoCodeStatus === 'error'"
          >
            <span class="spinner" v-show="promoCodeStatus === 'loading'"></span>
            <span class="btn-text" :class="{ hidden: promoCodeStatus === 'loading' }">ДОБАВИТЬ</span>
          </button>
        </div>

        <div v-if="promoCode" class="applied-promo">
          <span>Промокод "{{ promoCode }}" применен. Скидка {{ discountPercent }}%</span>
          <button @click="handleRemovePromoCode" class="remove-promo-btn">✕</button>
        </div>

        <div class="cart-items">
          <div
            v-for="item in cart.items"
            :key="item.id"
            class="cart-item"
            :class="{ loading: isItemLoading(item.product_id) }"
          >
            <div class="item-image">
              <img :src="getImageUrl(item.image_url)" :alt="item.product_name" @error="handleImageError" />
            </div>
            <div class="item-info">
              <div class="item-name">{{ item.product_name }}</div>
              <CartQuantityControl
                :product-id="item.product_id"
                :max-quantity="getAvailableQuantity(item.product_id)"
                :disabled="isItemLoading(item.product_id)"
                variant="cart"
              />
              <div class="item-price">{{ formatPrice(item.price) }}</div>
              <div class="item-stock">В наличии {{ getAvailableQuantity(item.product_id) }} шт.</div>
            </div>
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
      <div class="cart-checkout">
        <button
          @click="openCheckout"
          class="checkout-btn"
          :disabled="!cart?.items?.length || !remainingTime"
        >
          ОПЛАТИТЬ {{ formatPrice(finalTotal) }}
        </button>
      </div>
      <CheckoutModal v-if="showCheckoutModal" :isOpen="showCheckoutModal" @close="showCheckoutModal = false" />
    </template>
  </div>
</template>

<style>
@import "@/assets/styles/cart.css";
</style>