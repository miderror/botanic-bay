import { apiClient } from "@/services/httpClient.ts";
import type { IUserDiscount, IUserMonthlyOrders, IUserProfile } from "@/types/user.ts";
import { logger } from "@/utils/logger.ts";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

export const useUserStore = defineStore("userData", () => {
  // ==== DATA STATE ====
  const profile = ref<IUserProfile | null>(null);
  const discount = ref<IUserDiscount | null>(null);
  const monthlyOrdersAmount = ref<number | null>(null);

  // UI
  const isLoading = ref<boolean>(false);

  // Computed
  const discountPercentageDone = computed(() => {
    const d = discount.value;
    if (!d || !d.required_total) return 0;
    const passed = d.required_total - d.amount_left;
    return Math.min(100, Math.max(0, (passed / d.required_total) * 100));
  });

  // ==== ACTIONS ====
  const fetchProfile = async () => {
    try {
      logger.info("Fetching user profile");
      profile.value = await apiClient.get<IUserProfile>("/user/profile");
    } catch (error) {
      logger.error("Failed to fetch user profile", { error });
      throw error;
    }
  };

  const updateName = async (full_name: string) => {
    try {
      logger.info("Updating profile name");
      profile.value = await apiClient.patch<IUserProfile>("/user/profile", { full_name: full_name });
    } catch (error) {
      logger.error("Failed to update profile name", { error });
      throw error;
    }
  };

  const updatePhone = async (phone_number: string) => {
    try {
      logger.info("Updating profile phone number");
      profile.value = await apiClient.patch<IUserProfile>("/user/profile", {
        phone_number: phone_number,
      });
    } catch (error) {
      logger.error("Failed to update profile phone number", { error });
      throw error;
    }
  };

  const updateEmail = async (email: string) => {
    try {
      logger.info("Updating profile email");
      profile.value = await apiClient.patch<IUserProfile>("/user/profile", { email: email });
    } catch (error) {
      logger.error("Failed to update profile email", { error });
      throw error;
    }
  };

  const fetchDiscount = async () => {
    try {
      logger.info("Fetching user discount progress");
      discount.value = await apiClient.get<IUserDiscount>("/user/discount-progress");
    } catch (error) {
      logger.error("Failed to fetch user discount progress", { error });
      throw error;
    }
  };

  const fetchMonthlyOrders = async () => {
        try {
            logger.info("Fetching user monthly orders amount");
            const result = await apiClient.get<IUserMonthlyOrders>("/user/monthly-orders");
            monthlyOrdersAmount.value = result.monthly_orders_amount ?? 0;
        } catch (error) {
            logger.error("Failed to fetch user monthly orders amount", { error });
            throw error;
        }
    };

  return {
    // state
    isLoading,
    profile,
    discount,
    monthlyOrdersAmount,
    discountPercentageDone,

    // actions
    fetchProfile,
    updateName,
    updatePhone,
    updateEmail,
    fetchDiscount,
    fetchMonthlyOrders,
  };
});
