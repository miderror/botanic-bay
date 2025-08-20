<script setup lang="ts">
/**
 * Компонент для отображения реферала в swiper
 * @param {IReferral} item - реферал для отображения
 */
import CartIcon from "@/assets/images/cart.svg";
import ChevronIcon from "@/assets/images/chevron.svg";
import BusinessUserAvatar from "@/components/business/BusinessUserAvatar.vue";
import { useBusinessStore } from "@/stores/business.ts";
import type { IReferral } from "@/types/business.ts";

const props = defineProps<{
  item: IReferral;
}>();

const store = useBusinessStore();
const { openReferralDetails } = store;

const onItemClick = () => {
  openReferralDetails(props.item.id);
};
</script>

<template>
  <div
    class="business-swiper-item"
    @click="onItemClick"
  >
    <div class="business-user-info business-swiper-item__content">
      <BusinessUserAvatar
        :color="item.item_color || '#ccc'"
        class="business-user-info__icon"
      />
      <p class="business-user-info__name">
        {{ item.full_name }}
      </p>
      <div class="business-user-info__data">
        <p>Количество покупок в текущем месяце</p>
        <div class="business-user-info__data-value business-user-info__month-value">
          <img
            :src="CartIcon"
            class="business-user-info__month-icon"
          />
          <span>{{ item.current_month_orders }}</span>
        </div>
      </div>
      <div class="business-user-info__data">
        <p>Реферальный бонус</p>
        <div class="business-user-info__data-value">
          <span :style="{ backgroundColor: item.item_color }"> +{{ item.referral_bonus }} </span>
        </div>
      </div>
    </div>
    <div class="business-invited">
      <p>ПРИГЛАСИЛ: {{ item.referrals_count ?? 0 }}</p>
      <img :src="ChevronIcon" />
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/business.css";
@import "@/assets/styles/business-swiper.css";
</style>
