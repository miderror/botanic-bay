import { defineStore } from "pinia";
import { ref } from "vue";

export const useSearchStore = defineStore("search", () => {
  // Состояние активности поиска
  const isSearchActive = ref(false);

  // Текущий поисковый запрос
  const searchQuery = ref("");

  // Методы для управления состоянием
  const setSearchActive = (active: boolean) => {
    isSearchActive.value = active;
  };

  const setSearchQuery = (query: string) => {
    searchQuery.value = query;
  };

  const resetSearch = () => {
    isSearchActive.value = false;
    searchQuery.value = "";
  };

  return {
    // Состояние
    isSearchActive,
    searchQuery,

    // Методы
    setSearchActive,
    setSearchQuery,
    resetSearch,
  };
});
