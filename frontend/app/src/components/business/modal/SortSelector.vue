<script setup lang="ts">
/**
 * Компонент для выбора типа сортировки.
 */
import type { SortType } from "@/constants/sorting";

defineProps<{
  sortTypes: readonly SortType[];
  selectedSortType: SortType;
}>();

defineEmits<{
  (e: "select", sortType: SortType): void;
}>();
</script>

<template>
  <div class="sort-selector">
    <div
      class="sort-scroll"
      ref="scrollContainer"
    >
      <button
        v-for="(sortType, index) in sortTypes"
        :key="sortType"
        class="sort-btn"
        :class="{
          active: selectedSortType === sortType,
          'first-btn': index === 0,
          'last-btn': index === sortTypes.length - 1,
        }"
        @click="$emit('select', sortType)"
      >
        <span :title="sortType">{{ sortType }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Селектор категорий */
.sort-selector {
  /* width: 100%; */
  overflow: hidden;
  position: relative;
  padding: 0;
  display: flex;
  justify-content: center;
}

/* Скроллируемый контейнер категорий */
.sort-scroll {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  -ms-overflow-style: none;
  padding: 0 16px;
  max-width: fit-content;
}

.sort-btn {
  min-width: 80px;
  height: 24px;
  padding: 0 14px;
  background: #000;
  border: none;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-radius: 0;
  flex-shrink: 0;
}

/* Текст в кнопке */
.sort-btn span {
  text-align: center;
  color: white;
  font-size: 8px;
  font-family: var(--font-inter);
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.08px;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* Закругления для крайних кнопок */
.sort-btn.first-btn {
  border-top-left-radius: 100px;
  border-bottom-left-radius: 100px;
}

.sort-btn.last-btn {
  border-top-right-radius: 100px;
  border-bottom-right-radius: 100px;
}

/* Активная кнопка */
.sort-btn.active {
  background: var(--catalog-category-active);
}
</style>
