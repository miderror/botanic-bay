<script setup lang="ts">
import { useCart } from "@/composables/useCart";
import { useProductPolling } from "@/composables/useProductPolling";
import { logger } from "@/utils/logger";
import { debounce } from "lodash-es";
import { computed, onUnmounted, ref } from "vue";

interface Props {
  productId: string;
  maxQuantity: number;
  disabled?: boolean;
  variant?: "default" | "cart"; // Добавляем опцию варианта отображения
}

const props = defineProps<Props>();

// Состояние для блокировки кнопок во время обновления
const isUpdating = ref(false);

// Получаем методы работы с корзиной
const { cart, removeFromCart, updateQuantity } = useCart();

// Инициализируем polling для обновления количества
const { availableQuantity } = useProductPolling(props.productId);

// Получаем текущее количество товара в корзине
const currentQuantity = computed(() => {
  const item = cart.value?.items.find((item) => item.product_id === props.productId);
  return item?.quantity || 0;
});

// Проверяем возможность увеличения количества
const canIncrease = computed(() => {
  const maxAvailable = availableQuantity.value ?? 0;
  const actualAvailable = maxAvailable + currentQuantity.value;
  return currentQuantity.value < actualAvailable;
});

// Дебаунсированная функция обновления количества
const debouncedUpdateQuantity = debounce(async (productId: string, newQuantity: number) => {
  try {
    isUpdating.value = true;

    if (newQuantity === 0) {
      await removeFromCart(productId);
      logger.info("Product removed from cart", { productId });
    } else {
      await updateQuantity(productId, newQuantity);
      logger.info("Product quantity updated", {
        productId,
        newQuantity,
      });
    }
  } catch (err) {
    logger.error("Failed to update quantity", {
      productId,
      quantity: newQuantity,
      error: err,
    });
  } finally {
    isUpdating.value = false;
  }
}, 300);

// Обработчики кнопок
const handleDecrease = () => {
  if (isUpdating.value) return;

  const newQuantity = currentQuantity.value - 1;
  debouncedUpdateQuantity(props.productId, newQuantity);
};

const handleIncrease = () => {
  if (isUpdating.value || !canIncrease.value) {
    logger.warn("Cannot increase quantity", {
      productId: props.productId,
      currentQuantity: currentQuantity.value,
      availableStock: availableQuantity.value,
      isUpdating: isUpdating.value,
      canIncrease: canIncrease.value,
    });
    return;
  }

  const newQuantity = currentQuantity.value + 1;
  debouncedUpdateQuantity(props.productId, newQuantity);
};

// Очистка при размонтировании
onUnmounted(() => {
  debouncedUpdateQuantity.cancel();
});
</script>

<template>
  <div
    class="quantity-control-widget"
    :class="['quantity-control-widget--expanded', { 'quantity-control-widget--cart': variant === 'cart' }]"
  >
    <div class="quantity-control-widget__buttons">
      <button
        class="quantity-control-widget__btn"
        :disabled="disabled || isUpdating"
        @click="handleDecrease"
      >
        <div class="quantity-control-widget__minus-icon"></div>
      </button>

      <span class="quantity-control-widget__count">{{ currentQuantity }}</span>

      <button
        class="quantity-control-widget__btn"
        :disabled="disabled || !canIncrease || isUpdating"
        @click="handleIncrease"
      >
        <div class="quantity-control-widget__plus-icon"></div>
      </button>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/quantity-control.css";
</style>
