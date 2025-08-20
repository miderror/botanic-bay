<script setup lang="ts">
/**
 * Компонент для выбора типа сортировки и поиска.
 * При активации поиска скрывает селектор сортировки.
 */
import { DEFAULT_SORT_TYPE, SORT_TYPE_OPTIONS, type SortType } from "@/constants/sorting";
import { ref, watch } from "vue";
import SortSelector from "./SortSelector.vue";
import UserSearchBar from "./UserSearchBar.vue";

defineProps<{
  showNoResults?: boolean;
}>();

const selectedSortType = ref<SortType>(DEFAULT_SORT_TYPE);
const sortTypes = SORT_TYPE_OPTIONS;
const searchQuery = ref("");
const isSearchActive = ref(false);

// Эмиты для связи с родительским компонентом
const emit = defineEmits<{
  sortChange: [sortType: SortType];
  searchChange: [query: string];
  searchStateChange: [isActive: boolean];
  searchClear: [];
}>();

// Отслеживание изменений сортировки
watch(selectedSortType, (newSortType) => {
  emit("sortChange", newSortType);
});

// Отслеживание изменений поиска
watch(searchQuery, (newQuery) => {
  // Эмитим событие поиска только если длина запроса >= 3 символа или если запрос пустой (очистка)
  if (newQuery.trim().length >= 3 || newQuery.trim().length === 0) {
    emit("searchChange", newQuery);
  }
});

// Отслеживание состояния поиска
watch(isSearchActive, (newState) => {
  emit("searchStateChange", newState);
});

const handleSearchStateChange = (isActive: boolean) => {
  isSearchActive.value = isActive;
};
</script>

<template>
  <div style="display: flex; gap: 0px; align-items: center; justify-content: center">
    <SortSelector
      v-if="!isSearchActive"
      :sortTypes="sortTypes"
      :selectedSortType="selectedSortType"
      @select="(sortType) => (selectedSortType = sortType)"
      style="margin-top: 0; padding-top: 0"
    />
    <UserSearchBar
      v-model="searchQuery"
      :showNoProducts="showNoResults"
      @searchStateChange="handleSearchStateChange"
      @clear="emit('searchClear')"
    />
  </div>
</template>
