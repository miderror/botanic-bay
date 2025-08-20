<script lang="ts" setup>
import BaseModal from "@/components/common/BaseModal.vue";
import { useBusinessStore } from "@/stores/business";
import { storeToRefs } from "pinia";

const store = useBusinessStore();
const { isConditionsModalOpen } = storeToRefs(store);
const { confirmConditions } = store;

const onButtonClick = () => {
  confirmConditions();
};
</script>

<template>
  <BaseModal
    :model-value="isConditionsModalOpen"
    fullscreen
    title="УСЛОВИЯ РЕФЕРАЛЬНОЙ ПРОГРАММЫ"
    @update:modelValue="store.isConditionsModalOpen = $event"
  >
    <div class="business-modal">
      <p class="business-modal__text">Lorem Ipsum ...</p>
      <button
        class="business-modal__button"
        @click="onButtonClick"
      >
        Хочу зарабатывать!
      </button>
    </div>
  </BaseModal>
</template>

<style>
@import "@/assets/styles/business-modal.css";
</style>
