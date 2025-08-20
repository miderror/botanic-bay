<script setup lang="ts">
/**
 * Главный компонент приложения
 */
import NavigationBar from "@/components/common/NavigationBar.vue";
import { useCart } from "@/composables/useCart";
import { useNotification } from "@/composables/useNotification";
import { useTelegramWebApp } from "@/composables/useTelegramWebApp";
import { useViewport } from "@/composables/useViewport";
import { useAuthStore } from "@/stores/auth";
import { logger } from "@/utils/logger";
import { onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";

const { isKeyboardVisible } = useViewport();

const { initCart } = useCart();

const authStore = useAuthStore();
const { showNotification } = useNotification();
const router = useRouter();
const { isAvailable, user, error, isLoading } = useTelegramWebApp();

console.log("isAvailable:", isAvailable.value);
console.log("user:", user.value);
console.log("error:", error.value);

// Обработчик события успешной оплаты
const handlePaymentCompleted = (event: CustomEvent) => {
  logger.info("Payment completed event received", event.detail);

  // Проверяем наличие данных о платеже
  if (event.detail && event.detail.success) {
    // Показываем уведомление об успешной оплате
    showNotification("Оплата успешно завершена!", "success");

    // Перенаправляем на страницу заказов
    router.push({ name: "profile-orders" });
  }
};

onMounted(async () => {
  // Ждем инициализации Telegram WebApp
  if (isLoading.value) {
    return;
  }

  // Запрещаем глобально сворачивание Telegram WebApp вертикальными свайпами
  if (window.Telegram?.WebApp) {
    window.Telegram?.WebApp.disableVerticalSwipes();
  }

  // Определяем функцию установки высоты приложения
  const setAppHeight = () => {
    document.documentElement.style.setProperty("--app-height", `${window.innerHeight}px`);
  };

  // Добавляем слушатель изменения размера окна
  window.addEventListener("resize", setAppHeight);
  setAppHeight();

  // Добавляем слушатель события успешной оплаты
  window.addEventListener("payment-completed", handlePaymentCompleted as EventListener);

  // Сохраняем функцию для последующего удаления при размонтировании
  const cleanup = () => {
    window.removeEventListener("resize", setAppHeight);
    window.removeEventListener("payment-completed", handlePaymentCompleted as EventListener);
  };

  // Устанавливаем функцию очистки для onUnmounted
  onUnmounted(cleanup);

  // Загрузка шрифтов
  try {
    await document.fonts.ready;
    console.log("Fonts loaded successfully");
    console.log(
      "Available fonts:",
      Array.from(document.fonts).map((f) => f.family),
    );
  } catch (error) {
    console.error("Error loading fonts:", error);
  }

  if (user.value) {
    console.log("Вызываем register");
    await authStore.register();
    // Добавляем инициализацию корзины после регистрации
    await initCart();
  }
  await router.push("/catalog");
});
</script>

<template>
  <div
    :class="{
      'telegram-app': isAvailable,
      'keyboard-visible': isKeyboardVisible,
    }"
  >
    <div
      v-if="error"
      class="error"
    >
      Ошибка инициализации: {{ error }}
    </div>

    <div
      v-else-if="isLoading"
      class="loading"
    >
      Загрузка...
    </div>

    <template v-else>
      <RouterView />
      <NavigationBar />
    </template>
  </div>
</template>
