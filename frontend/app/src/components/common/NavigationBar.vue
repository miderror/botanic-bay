<script setup lang="ts">
/**
 * Компонент нижней навигационной панели
 * Отображает навигацию по основным разделам приложения и кнопку оплаты
 * в режиме оформления заказа
 */
import LoadingOverlay from "@/components/common/LoadingOverlay.vue";
import AdminIcon from "@/components/icons/AdminIcon.vue";
import CartIcon from "@/components/icons/CartIcon.vue";
import CatalogIcon from "@/components/icons/CatalogIcon.vue";
import ProfileIcon from "@/components/icons/ProfileIcon.vue";
import { useCart } from "@/composables/useCart";
import { useCheckout } from "@/composables/useCheckout";
import { useNotification } from "@/composables/useNotification";
import { useAuthStore } from "@/stores/auth";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import { computed } from "vue";

const authStore = useAuthStore();
const { itemsCount } = useCart();
const { showNotification } = useNotification();

// Используем композабл для checkout
const { isCheckoutActive, canPay, totalAmount, processPayment, isPaymentProcessing } = useCheckout();

// Проверяем права администратора
const isAdmin = computed(() => authStore.isAdmin);

/**
 * Обработчик нажатия кнопки оплаты
 * Запускает процесс создания заказа и оплаты
 */
const handlePay = async () => {
  try {
    logger.info("Payment button clicked in NavigationBar");

    // Вызываем функцию обработки платежа из useCheckout
    // Эта функция уже включает в себя создание заказа и инициализацию платежа
    await processPayment();

    // Примечание: обработка успешного платежа происходит через глобальные события
    // в App.vue (handlePaymentCompleted)
  } catch (error) {
    logger.error("Error in navigation bar payment handling", { error });
    showNotification("Произошла ошибка при обработке платежа", "error");
  }
};
</script>

<template>
  <nav
    class="navigation-bar"
    :class="{
      'navigation-bar--checkout': isCheckoutActive,
    }"
  >
    <!-- Основная навигация -->
    <template v-if="!isCheckoutActive">
      <router-link
        to="/catalog"
        class="nav-item"
        active-class="active"
      >
        <CatalogIcon class="nav-icon" />
        <span class="nav-text">КАТАЛОГ</span>
      </router-link>

      <router-link
        to="/cart"
        class="nav-item"
        active-class="active"
      >
        <div class="icon-container">
          <CartIcon class="nav-icon" />
          <span
            v-if="itemsCount"
            class="cart-counter"
          >
            {{ itemsCount }}
          </span>
        </div>
        <span class="nav-text">ЗАКАЗЫ</span>
      </router-link>

      <router-link
        to="/profile"
        class="nav-item"
        active-class="active"
      >
        <ProfileIcon class="nav-icon" />
        <span class="nav-text">ЛИЧНЫЙ КАБИНЕТ</span>
      </router-link>

      <router-link
        v-if="isAdmin"
        to="/admin"
        class="nav-item"
        active-class="active"
      >
        <AdminIcon class="nav-icon" />
        <span class="nav-text">УПРАВЛЕНИЕ</span>
      </router-link>
    </template>

    <!-- Навигация в режиме оформления заказа -->
    <template v-else>
      <button
        class="checkout-pay-button"
        :class="{ disabled: !canPay }"
        :disabled="!canPay"
        @click="handlePay"
      >
        <span class="checkout-pay-text"> ЗАПЛАТИТЬ {{ formatPrice(totalAmount) }} </span>
      </button>
    </template>
  </nav>

  <!-- Оверлей загрузки при обработке платежа -->
  <LoadingOverlay
    :visible="isPaymentProcessing"
    message="Подготовка платежной формы..."
  />
</template>

<style>
@import "@/assets/styles/navigation.css";
</style>
