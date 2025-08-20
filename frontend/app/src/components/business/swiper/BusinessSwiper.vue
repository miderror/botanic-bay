<script setup lang="ts">
/**
 * Компонент для отображения слайдера приглашенных пользователей в бизнес-разделе.
 */
import BusinessSwiperItem from "@/components/business/swiper/BusinessSwiperItem.vue";
import type { IReferral } from "@/types/business.ts";
import "swiper/css";
import { Swiper, SwiperSlide } from "swiper/vue";

defineProps<{
  items: IReferral[];
}>();
</script>

<template>
  <Swiper
    class="business-swiper-container"
    :space-between="10"
    :slides-per-view="1.8"
    :centered-slides="true"
    :centered-slides-bounds="true"
  >
    <SwiperSlide
      v-for="(item, index) in items"
      :key="index"
    >
      <BusinessSwiperItem :item="item" />
    </SwiperSlide>
  </Swiper>
</template>

<style>
@import "@/assets/styles/business-swiper.css";
</style>
