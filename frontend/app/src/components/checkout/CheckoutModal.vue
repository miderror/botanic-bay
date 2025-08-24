<script setup lang="ts">
/**
 * Компонент модального окна оформления заказа
 * Отображает корзину, способ доставки и оплаты, позволяет завершить заказ
 */
import yookassaLogo from "@/assets/images/yookassa-logo-black.svg";
import BaseModal from "@/components/common/BaseModal.vue";
import LoadingOverlay from "@/components/common/LoadingOverlay.vue";
import DeliverySection from "@/components/delivery-section/DeliverySection.vue";
import { useCart } from "@/composables/useCart";
import { useCheckout } from "@/composables/useCheckout";
import { useNotification } from "@/composables/useNotification";
import { useCheckoutStore } from "@/stores/checkout";
import { PaymentMethod } from "@/types/order";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import { computed, onMounted, onUnmounted } from "vue";

// Пропсы и эмиты
defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

// Композаблы
const checkoutStore = useCheckoutStore();
const { showNotification } = useNotification();
const { cart } = useCart();
const {
  canPay,
  startCheckout,
  finishCheckout,
  setPaymentMethod,
  processPayment,
  isPaymentProcessing,
  totalAmount,
  deliveryCost,
  isCalculatingDelivery,
} = useCheckout();

/**
 * Товары в корзине для отображения
 */
const cartItems = computed(() => cart.value?.items || []);

/**
 * Обработчик закрытия модального окна оформления заказа
 */
const handleClose = () => {
  finishCheckout();
  emit("close");
  logger.debug("Checkout modal closed");
};

/**
 * Обработчик нажатия кнопки оплаты
 * Запускает процесс создания заказа и инициализации платежа
 */
const handlePay = async () => {
  try {
    logger.info("handlePay: Pay button clicked in CheckoutModal");

    // Дополнительные проверки перед инициацией платежа
    if (typeof document === "undefined" || !document.createElement) {
      throw new Error("handlePay: DOM not available");
    }

    if (!window || typeof window.addEventListener !== "function") {
      throw new Error("handlePay: Window object not properly initialized");
    }

    // Запускаем процесс оплаты через композабл useCheckout
    // Эта функция содержит логику создания заказа и инициализации платежа
    const success = await processPayment();

    if (success) {
      logger.info("handlePay: Payment process started successfully");
      // Не закрываем модальное окно сразу, т.к. открывается виджет оплаты
      // Закрытие произойдет автоматически после успешной оплаты через обработчики событий
    } else {
      logger.warn("handlePay: Payment process failed or was cancelled");
    }
  } catch (error) {
    console.error("❌ handlePay: Error in checkout modal payment handling", { error });
    showNotification("Произошла ошибка при обработке платежа", "error");
  }
};

onMounted(() => {
  // Активируем режим оформления заказа
  try {
    startCheckout();
  } catch (error) {
    console.error("❌ Error activating checkout mode", { error });
    showNotification("Не удалось активировать режим оформления заказа", "error");
    return;
  }

  // Автоматически выбираем YooKassa как единственный доступный способ оплаты
  try {
    setPaymentMethod(PaymentMethod.YOOKASSA);
  } catch (error) {
    console.error("❌ Error setting payment method", { error });
    showNotification("Не удалось установить способ оплаты", "error");
    return;
  }

  // Загружаем сохраненное состояние
  try {
    checkoutStore.loadSavedState();
  } catch (error) {
    console.error("❌ Error loading saved checkout state", { error });
    showNotification("Не удалось загрузить сохраненное состояние оформления заказа", "error");
  }

  logger.debug("Checkout modal mounted, payment method set to YooKassa");
});

onUnmounted(() => {
  // Деактивируем режим оформления заказа при закрытии
  finishCheckout();
  logger.debug("Checkout modal unmounted");
});
</script>

<template>
  <BaseModal
    :modelValue="isOpen"
    @update:modelValue="handleClose"
    title="Оформление заказа"
    fullscreen
  >
    <div class="basket-order">
      <!-- Секция способа доставки -->
      <DeliverySection />

      <!-- Секция товаров -->
      <section class="order-items">
        <div
          v-for="(item, index) in cartItems"
          :key="item.id"
          class="order-item"
          :class="{
            'single-item': cartItems.length === 1,
            'first-item': cartItems.length > 1 && index === 0,
            'last-item': cartItems.length > 1 && index === cartItems.length - 1,
          }"
        >
          <div class="item-image-container">
            <img
              :src="item.image_url || '/images/placeholder.jpg'"
              :alt="item.product_name"
              class="item-image"
            />
          </div>
          <span class="item-quantity">{{ item.quantity }} шт.</span>
          <span class="delivery-date">Завтра</span>
        </div>
      </section>

      <!-- Секция способа оплаты -->
      <section class="checkout-section">
        <h2 class="section-title">Способ оплаты</h2>
        <div class="payment-section">
          <div class="payment-cards">
            <div class="cards-row">
              <div class="card-frame">
                <div class="card-slot active">
                  <img
                    :src="yookassaLogo"
                    class="payment-logo"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Итоговая сумма -->
      <div class="checkout-total-amount">
        <span>Стоимость товаров:</span>
        <span>{{ formatPrice(cart?.total || 0) }}</span>
      </div>
      <div class="checkout-total-amount">
        <span>Доставка:</span>
        <span v-if="isCalculatingDelivery">Расчет...</span>
        <span v-else-if="deliveryCost !== null">{{ formatPrice(deliveryCost) }}</span>
        <span v-else>Выберите адрес</span>
      </div>

      <div v-if="checkoutStore.promoCode" class="checkout-total-amount promo-discount">
        <span>Скидка по промокоду:</span>
        <span>- {{ formatPrice((cart?.total || 0) * (checkoutStore.discountPercent / 100)) }}</span>
      </div>

    <div v-if="checkoutStore.userDiscountPercent > 0" class="checkout-total-amount personal-discount">
      <span>Персональная скидка ({{ checkoutStore.userDiscountPercent }}%):</span>
      <span>- {{ formatPrice((cart?.total || 0) * (checkoutStore.userDiscountPercent / 100)) }}</span>
    </div>

      <div class="checkout-total-amount final-total">
        <span>Общая сумма заказа:</span>
        <span>{{ formatPrice(totalAmount) }}</span>
      </div>

      <!-- Кнопка оплаты -->
      <div class="checkout-navbar">
        <button
          class="pay-button"
          :class="{ disabled: !canPay }"
          :disabled="!canPay"
          @click="handlePay"
        >
          <span class="pay-button-text"> ЗАПЛАТИТЬ {{ formatPrice(totalAmount) }} </span>
        </button>
      </div>
    </div>
  </BaseModal>

  <!-- Оверлей загрузки при обработке платежа -->
  <LoadingOverlay
    :visible="isPaymentProcessing"
    message="Подготовка платежной формы..."
  />
</template>

<style>
@import "@/assets/styles/modal.css";
@import "@/assets/styles/checkout.css";
.promo-discount {
  color: #66ca1a;
}
.personal-discount {
  color: #66ca1a;
}
</style>
