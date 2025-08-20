<script lang="ts" setup>
/**
 * Компонент модального окна со списком всех приглашенных по рефералу пользователей.
 */
import BusinessReferralList from "@/components/business/referral-list/BusinessReferralList.vue";
import BaseModal from "@/components/common/BaseModal.vue";
import { useBusinessStore } from "@/stores/business.ts";
import { storeToRefs } from "pinia";
import SortAndFilterControl from "./SortAndFilterControl.vue";
import { ref } from "vue";
import { DEFAULT_SORT_TYPE, type SortType } from "@/constants/sorting";

const store = useBusinessStore();
const { profile, isAllPartnersModalOpen, invitedUsers, hasSearchResults } = storeToRefs(store);
const { loadMoreInvited, sortInvited, searchInvited, fetchInvited, resetSearchState } = store;

// Состояние поиска и сортировки
const currentSortType = ref<SortType>(DEFAULT_SORT_TYPE);
const currentSearchQuery = ref("");
const isSearchActive = ref(false);

// Обработчик изменения сортировки
const handleSortChange = (sortType: string) => {
  currentSortType.value = sortType as SortType;
  if (!isSearchActive.value) {
    sortInvited(sortType as SortType);
  }
};

// Обработчик изменения поиска
const handleSearchChange = (query: string) => {
  currentSearchQuery.value = query;
  if (query.trim()) {
    searchInvited(query.trim());
  } else if (!isSearchActive.value) {
    // Если поиск очищен и поиск не активен, загружаем обычный список и сортируем
    resetSearchState();
    fetchInvited().then(() => {
      sortInvited(currentSortType.value);
    });
  }
};

// Обработчик изменения состояния поиска
const handleSearchStateChange = (isActive: boolean) => {
  isSearchActive.value = isActive;
  if (!isActive && !currentSearchQuery.value.trim()) {
    // Если поиск деактивирован и нет поискового запроса,
    // загружаем обычный список и применяем сортировку
    resetSearchState();
    fetchInvited().then(() => {
      sortInvited(currentSortType.value);
    });
  }
};

// Обработчик очистки поиска
const handleSearchClear = () => {
  currentSearchQuery.value = "";
  isSearchActive.value = false;
  // Загружаем обычный список и применяем сортировку
  resetSearchState();
  fetchInvited().then(() => {
    sortInvited(currentSortType.value);
  });
};
</script>

<template>
  <BaseModal
    :model-value="isAllPartnersModalOpen"
    fullscreen
    @close="store.isAllPartnersModalOpen = false"
    @update:modelValue="store.isAllPartnersModalOpen = $event"
    title="Все приглашенные пользователи"
  >
    <SortAndFilterControl
      :showNoResults="isSearchActive && !hasSearchResults"
      @sortChange="handleSortChange"
      @searchChange="handleSearchChange"
      @searchStateChange="handleSearchStateChange"
      @searchClear="handleSearchClear"
    />

    <div class="business-item-modal business-item-modal_all">
      <BusinessReferralList
        :items="invitedUsers"
        @scroll-end="loadMoreInvited"
      />

      <div class="business-invited">
        <p>Общий реферальный бонус</p>
        <span>+{{ profile?.referral_bonus ?? 0 }}</span>
      </div>
    </div>
  </BaseModal>
</template>

<style>
@import "@/assets/styles/business-item-modal.css";
</style>
