<script setup lang="ts">
import UserIcon from "@/assets/images/user.svg";
import { useBusinessStore } from "@/stores/business.ts";
import type { IReferral } from "@/types/business.ts";
import { onMounted, ref } from "vue";
import BusinessUserAvatar from "./BusinessUserAvatar.vue";

const props = defineProps<{
  item: IReferral;
  itemColor?: string;
}>();

const store = useBusinessStore();
const { getRandomItemColor, openReferralDetails } = store;

const color = ref<string | undefined>(props.itemColor);

onMounted(() => {
  if (color.value) return;
  color.value = getRandomItemColor();
});
</script>

<template>
  <div
    class="business-invited-users__item"
    @click="() => openReferralDetails(item.id)"
  >
    <div class="business-invited-users__item-data-block">
      <BusinessUserAvatar
        :style="{ color: color }"
        class="business-invited-users__item-icon"
      />
      <div class="business-invited-users__item-info">
        <p>{{ item.full_name }}</p>
        <span>Увеличивает ваш бонус</span>
      </div>
    </div>
    <div class="business-invited-users__item-bonus-block">
      <div class="business-invited-users__item-partners-wrapper">
        <div class="business-invited-users__item-partners">
          <p>+{{ item.referrals_count ?? 0 }}</p>
          <img
            :src="UserIcon"
            class="business-invited-users__item-user-icon"
          />
        </div>
      </div>
      <div class="business-invite-users__item-bonus-wrapper">
        <span
          class="business-invited-users__item-bonus"
          :style="{ backgroundColor: color }"
        >
          +{{ item.referral_bonus }}
        </span>
      </div>
    </div>
  </div>
</template>
