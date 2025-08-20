<script setup lang="ts">
import BusinessUserIcon from "@/assets/images/business-user.svg";
import CartIcon from "@/assets/images/cart.svg";
import { useBusinessStore } from "@/stores/business.ts";
import { storeToRefs } from "pinia";

const store = useBusinessStore();
const { selectedReferral } = storeToRefs(store);
</script>

<template>
  <div class="business-user-info business-item-modal__user-card">
    <img
      :src="BusinessUserIcon"
      :style="{ color: selectedReferral?.item_color }"
      class="business-user-info__icon"
    />
    <p class="business-user-info__name">
      {{ selectedReferral?.full_name }}
    </p>
    <div class="business-user-info__data">
      <p>Количество покупок в<br />текущем месяце</p>
      <div class="business-user-info__data-value business-user-info__month-value">
        <img
          :src="CartIcon"
          class="business-user-info__month-icon"
        />
        <span>{{ selectedReferral?.current_month_orders }}</span>
      </div>
    </div>
    <div class="business-user-info__data">
      <p>Реферальный бонус</p>
      <div class="business-user-info__data-value">
        <span :style="{ backgroundColor: selectedReferral?.item_color }">
          +{{ selectedReferral?.referral_bonus }}
        </span>
      </div>
    </div>
  </div>
</template>
