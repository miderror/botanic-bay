import type { TelegramUser } from "@/types/telegram";
import type { TelegramWebApp } from "@/types/telegram-webapp";
import { onMounted, ref } from "vue";

export function useTelegramWebApp() {
  const isAvailable = ref(false);
  const webApp = ref<TelegramWebApp | null>(null);
  const user = ref<TelegramUser | null>(null);
  const error = ref<string | null>(null);
  const isLoading = ref(true);

  onMounted(async () => {
    try {
      // Максимально подробное логирование
      console.log("Window object:", window);
      console.log("Telegram object:", window.Telegram);
      console.log("WebApp object:", window.Telegram?.WebApp);

      if (!window.Telegram) {
        throw new Error("Telegram object is not available in window");
      }

      if (!window.Telegram.WebApp) {
        throw new Error("Telegram WebApp is not available");
      }

      // Проверяем все возможные источники данных
      const webAppInstance = window.Telegram.WebApp;

      console.log("WebApp initDataUnsafe:", webAppInstance.initDataUnsafe);

      webApp.value = webAppInstance;
      isAvailable.value = true;

      // Извлекаем данные пользователя максимально безопасно
      const userData = webAppInstance.initDataUnsafe?.user;

      if (!userData) {
        throw new Error("No user data found in WebApp");
      }

      user.value = {
        id: userData.id,
        username: userData.username,
        first_name: userData.first_name,
        last_name: userData.last_name,
      };

      console.log("Extracted user:", user.value);

      webAppInstance.ready();
      webAppInstance.expand();
    } catch (err) {
      console.error("WebApp initialization error:", err);

      error.value = err instanceof Error ? err.message : "Unknown WebApp initialization error";
    } finally {
      isLoading.value = false;
    }
  });

  return {
    isAvailable,
    webApp,
    user,
    error,
    isLoading,
  };
}
