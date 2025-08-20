<script setup lang="ts">
import BusinessReferralListItem from "@/components/business/referral-list/BusinessReferralListItem.vue";
import type { IReferral } from "@/types/business.ts";

defineProps<{
  items: IReferral[];
}>();
</script>

<template>
  <RecycleScroller
    class="scroller business-invited-users"
    :items="items"
    :item-size="58"
    key-field="id"
    v-slot="{ item }"
    @scroll-end="$emit('scroll-end')"
  >
    <BusinessReferralListItem
      :item="item"
      :item-color="item.item_color"
    />
  </RecycleScroller>
</template>
