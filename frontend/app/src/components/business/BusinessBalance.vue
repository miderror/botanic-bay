<script setup lang="ts">
/**
 * Компонент для отображения баланса и заработка в бизнес-профиле
 * Включает кнопку для копирования реферальной ссылки и вывода заработанных средств
 */
import CoinsIcon from "@/assets/images/coins.svg";
import CopyIcon from "@/assets/images/copy.svg";
import { useBusinessStore } from "@/stores/business.ts";
import { storeToRefs } from "pinia";

const store = useBusinessStore();
const { isRegistered, isAbleToWithdraw, balance, isCopiedShown } = storeToRefs(store);
const { openConditionsFlow, copyLink, openWithdrawModal } = store;

const onEarnButtonClick = () => {
  if (isRegistered.value) {
    copyLink();
  } else {
    openConditionsFlow();
  }
};

const onWithdrawButtonClick = () => {
  if (!isAbleToWithdraw.value) return;
  openWithdrawModal();
};
</script>

<template>
  <p
    class="section-title"
    style="margin-bottom: 10px !important"
  >
    Вы заработали
  </p>
  <div class="business-balance">
    <div class="business-balance__info">
      <img :src="CoinsIcon" />
      <p class="business-balance__value">{{ balance }}р</p>
    </div>
    <button
      class="action-button"
      :disabled="!isAbleToWithdraw"
      @click="onWithdrawButtonClick"
    >
      Вывести
    </button>
  </div>
  <p class="business-text">Приглашай участников и зарабатывай % с их каждой покупки!</p>

  <div class="earn-button-container">
    <Transition name="link-copied-fade">
      <div
        class="link-copied"
        v-if="isCopiedShown"
      >
        <img :src="CopyIcon" />
        <p>Ссылка скопирована</p>
      </div>
    </Transition>

    <button
      class="earn-button"
      @click="onEarnButtonClick"
    >
      Поделись и заработай!
    </button>
  </div>
</template>
