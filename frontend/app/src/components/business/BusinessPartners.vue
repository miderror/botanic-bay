<script setup lang="ts">
/**
 * Компонент для отображения приглашенных пользователей в бизнес-разделе.
 */
import BusinessSwiper from "@/components/business/swiper/BusinessSwiper.vue";
import { useBusinessStore } from "@/stores/business.ts";
import { storeToRefs } from "pinia";

const store = useBusinessStore();
const { totalInvited, topInvitedUsers } = storeToRefs(store);
const { openAllReferrals } = store;
</script>

<template>
  <div class="business-partners">
    <p class="business-title">Приглашенные пользователи: {{ totalInvited }} чел.</p>
    <BusinessSwiper :items="topInvitedUsers" />
    <button
      v-if="totalInvited > topInvitedUsers.length"
      class="action-button action-button_show-all"
      @click="openAllReferrals"
    >
      СМОТРЕТЬ ВСЕХ
    </button>
  </div>
</template>

<style scoped>
@import "@/assets/styles/business.css";
</style>
