<script lang="ts" setup>
/**
 * Компонент модального окна с информацией об одном из приглашенных по рефералу пользователей.
 */
import UserIcon from "@/assets/images/user.svg";
import BusinessItemModalUserCard from "@/components/business/modal/item/BusinessItemModalUserCard.vue";
import BusinessReferralList from "@/components/business/referral-list/BusinessReferralList.vue";
import BaseModal from "@/components/common/BaseModal.vue";
import { useBusinessStore } from "@/stores/business.ts";
import { storeToRefs } from "pinia";

const store = useBusinessStore();
const { isItemModalOpen, selectedReferral, selectedChildren } = storeToRefs(store);
const { closeReferralDetailsAndReturnToAll } = store;
</script>

<template>
  <BaseModal
    :model-value="isItemModalOpen"
    fullscreen
    @close="closeReferralDetailsAndReturnToAll"
    @update:modelValue="!$event && closeReferralDetailsAndReturnToAll()"
  >
    <div class="business-item-modal">
      <BusinessItemModalUserCard />
      <BusinessReferralList :items="selectedChildren" />

      <div class="business-invited">
        <div class="business-invited__users">
          <p>ПРИГЛАСИЛ: +{{ selectedReferral?.referrals_count }}</p>
          <img
            :src="UserIcon"
            class="business-invited__user-icon"
          />
        </div>
        <div class="business-invited__bonus">
          <p>БОНУС:</p>
          <span>+{{ selectedReferral?.referral_bonus }}</span>
        </div>
      </div>
    </div>
  </BaseModal>
</template>

<style>
@import "@/assets/styles/business-item-modal.css";
</style>
