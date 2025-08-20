<script lang="ts" setup>
import CdekIcon from "@/components/icons/CdekIcon.vue";
import { useImageUrl } from "@/composables/useImageUrl";
import { useOrderFormatting } from "@/composables/useOrderFormatting";
import type { IOrder } from "@/types/order";

defineProps<{
  order: IOrder;
}>();

const { getImageUrl, handleImageError } = useImageUrl();
const { formatDeliveryDate } = useOrderFormatting();
</script>

<template>
  <div class="bb-order-card">
    <!-- Верхняя строка -->
    <div class="bb-order-card__header">
      <div class="bb-order-card__date">
        {{ formatDeliveryDate(order) }}
      </div>
      <div class="bb-order-card__dots">
        <div class="bb-order-card__dot"></div>
        <div class="bb-order-card__dot"></div>
        <div class="bb-order-card__dot"></div>
      </div>
    </div>

    <!-- Блок с СДЭК и адресом -->
    <div class="bb-order-card__delivery">
      <div class="bb-order-card__cdek-circle">
        <CdekIcon />
      </div>
      <div class="bb-order-card__address">
        {{ order?.delivery_point ?? order?.delivery_to_location?.address }}
      </div>
    </div>

    <!-- Товары -->
    <div class="bb-order-card__items">
      <div
        v-for="item in order.items"
        :key="item.id"
        class="bb-order-card__row"
      >
        <img
          :alt="item.product_name"
          :src="getImageUrl(item.image_url || null)"
          class="bb-order-card__image"
          @error="handleImageError"
        />
        <div class="bb-order-card__quantity">{{ item.quantity }} шт.</div>
        <div class="bb-order-card__payment">ОПЛАЧЕНО</div>
        <!-- <div v-if="order.status === 'paid'" class="bb-order-card__payment">
          ОПЛАЧЕНО
        </div> -->
      </div>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/order.css";
</style>
