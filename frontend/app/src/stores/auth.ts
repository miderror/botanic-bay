import type { IUser } from "@/types/user";
import { logger } from "@/utils/logger";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<IUser | null>(null);
  const isAuthenticated = ref(false);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  async function register() {
    logger.info("Starting registration...");
    isLoading.value = true;
    error.value = null;

    try {
      const webappData = window.Telegram?.WebApp?.initDataUnsafe;
      logger.info("WebApp data:", { webappData });

      if (!webappData?.user) {
        logger.error("No Telegram WebApp data available");
        throw new Error("No Telegram WebApp data available");
      }

      logger.info("Making registration request", {
        telegram_id: webappData.user.id,
        username: webappData.user.username,
        full_name: `${webappData.user.first_name} ${webappData.user.last_name || ""}`,
      });

      // const { referralCode } = useReferralCode()
      const referralCode = localStorage.getItem("referral_code");

      const response = await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          telegram_id: webappData.user.id,
          username: webappData.user.username || "",
          full_name: `${webappData.user.first_name} ${webappData.user.last_name || ""}`,
          referral_code: referralCode,
        }),
      });

      logger.info("Got response", {
        status: response.status,
        ok: response.ok,
      });

      if (!response.ok) {
        throw new Error("Registration failed");
      }

      // Правильное извлечение из структуры ответа
      const rawData = await response.json();
      logger.info("Raw response:", rawData);

      const userData = rawData.user;
      logger.info("UserData extracted:", userData);

      user.value = {
        ...userData,
        roles: userData.roles || [], // На всякий случай оставляем fallback
      };

      logger.info("User data after registration", {
        userId: userData.value.id,
        roles: userData.value.roles,
        isAdmin: hasRole("admin"),
      });

      logger.info("User registered", { userData });
      isAuthenticated.value = true;
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Unknown error";
    } finally {
      isLoading.value = false;
    }
  }

  const hasRole = (role: string) => {
    logger.info("Checking role", {
      role,
      currentRoles: user.value?.roles,
      hasRole: user.value?.roles?.includes(role),
    });
    return user.value?.roles?.includes(role) || false;
  };

  const isAdmin = computed(() => hasRole("admin"));

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    register,
    hasRole,
    isAdmin,
  };
});
