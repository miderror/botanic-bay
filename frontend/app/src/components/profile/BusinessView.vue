<script setup lang="ts">
/**
 * Компонент для отображения бизнес-профиля пользователя
 * Включает баланс, список партнеров и модальные окна для управления условиями и партнерскими
 * программами
 */
import BusinessBalance from "@/components/business/BusinessBalance.vue";
import BusinessPartners from "@/components/business/BusinessPartners.vue";
import BusinessAllPartnersModal from "@/components/business/modal/BusinessAllPartnersModal.vue";
import BusinessConditionsModal from "@/components/business/modal/BusinessConditionsModal.vue";
import BusinessTermsModal from "@/components/business/modal/BusinessTermsModal.vue";
import BusinessWithdrawModal from "@/components/business/modal/BusinessWithdrawModal.vue";
import BusinessItemModal from "@/components/business/modal/item/BusinessItemModal.vue";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import NotificationToast from "@/components/common/NotificationToast.vue";
import { useNotification } from "@/composables/useNotification.ts";
import { useBusinessStore } from "@/stores/business.ts";
import { storeToRefs } from "pinia";
import { onMounted } from "vue";

const store = useBusinessStore();
const { isTopInvitedLoading, totalInvited, isRegistered } = storeToRefs(store);
const { fetchProfile, fetchTopInvited, openTermsDirectly } = store;

const { show } = useNotification();

onMounted(async () => {
  await Promise.all([fetchProfile(), fetchTopInvited()]);
});
</script>

<template>
  <div class="business-section">
    <NotificationToast
      :show="show"
      :message="'message'"
      :type="'error'"
    />

    <BusinessBalance />

    <LoadingSpinner v-if="isTopInvitedLoading" />
    <BusinessPartners v-if="isRegistered && totalInvited > 0" />

    <button
      class="action-button action-button_conditions"
      v-if="isRegistered"
      @click="openTermsDirectly"
    >
      УСЛОВИЯ РЕФЕРАЛЬНОЙ СИСТЕМЫ
    </button>

    <BusinessConditionsModal />
    <BusinessTermsModal />
    <BusinessItemModal />
    <BusinessAllPartnersModal />
    <BusinessWithdrawModal />
  </div>
</template>

<style scoped>
@import "@/assets/styles/profile.css";
@import "@/assets/styles/business.css";
</style>
