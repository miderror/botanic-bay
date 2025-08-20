<script lang="ts" setup>
import BaseModal from "@/components/common/BaseModal.vue";
import { useBusinessStore } from "@/stores/business";
import { storeToRefs } from "pinia";
import { computed, ref } from "vue";

const store = useBusinessStore();
const { isTermsModalOpen, signedTerms } = storeToRefs(store);
const { confirmTerms, copyLink } = store;

const checkbox1 = ref(false);
const checkbox2 = ref(false);

const allChecked = computed(() => checkbox1.value && checkbox2.value);
const showButton = computed(() => !signedTerms.value);

const onButtonClick = () => {
  confirmTerms(copyLink);
};
</script>

<template>
  <BaseModal
    :model-value="isTermsModalOpen"
    fullscreen
    title="ПОЛЬЗОВАТЕЛЬСКОЕ СОГЛАШЕНИЕ"
    @close="store.isTermsModalOpen = false"
    @update:modelValue="store.isTermsModalOpen = $event"
  >
    <div class="business-modal">
      <p class="business-modal__text">
        Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem
        Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum
        Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum Lorem Ipsum
      </p>

      <div
        v-if="showButton"
        class="business-modal__checkboxes"
      >
        <label class="business-modal__checkbox-container">
          Lorem Ipsum Lorem Ipsum
          <input
            v-model="checkbox1"
            type="checkbox"
          />
          <span class="business-modal__checkbox-mark"></span>
        </label>
        <label class="business-modal__checkbox-container">
          Lorem Ipsum Lorem Ipsum
          <input
            v-model="checkbox2"
            type="checkbox"
          />
          <span class="business-modal__checkbox-mark"></span>
        </label>
      </div>

      <button
        v-if="showButton"
        :disabled="!allChecked"
        class="business-modal__button"
        @click="onButtonClick"
      >
        СОГЛАСИТЬСЯ И СКОПИРОВАТЬ ССЫЛКУ
      </button>
    </div>
  </BaseModal>
</template>

<style>
@import "@/assets/styles/business-modal.css";
</style>
