<script setup lang="ts">
/**
 * Компонент для отображения панели поиска товаров по названию.
 * При активации поиска отображает поле ввода и кнопку очистки.
 * При отсутствии результатов отображает сообщение с иконкой корзины.
 */
import CartIcon from "@/components/icons/CartIcon.vue";
import CloseIcon from "@/components/icons/CloseSearchIcon.vue";
import SearchIcon from "@/components/icons/SearchIcon.vue";
import { useSearch } from "@/composables/useSearch";
import { logger } from "@/utils/logger";
import { sanitizeSearchQuery } from "@/utils/sanitizer";
import { nextTick, ref, watch } from "vue";

const { isSearchActive, searchQuery } = useSearch();

interface SearchBarProps {
  modelValue: string;
  showNoProducts?: boolean;
}

interface SearchBarEmits {
  (e: "update:modelValue", value: string): void;
  (e: "search", query: string): void;
  (e: "searchStateChange", isActive: boolean): void;
  (e: "clear"): void;
}

const props = defineProps<SearchBarProps>();
const emit = defineEmits<SearchBarEmits>();

const searchInput = ref<HTMLInputElement | null>(null);

const activateSearch = async (): Promise<void> => {
  isSearchActive.value = true;
  emit("searchStateChange", true);

  // Ждем следующего тика для обновления DOM
  await nextTick();

  const focusInput = () => {
    if (searchInput.value) {
      // Пробуем установить фокус напрямую
      searchInput.value.focus();

      // Дополнительно пробуем через click для мобильных
      searchInput.value.click();

      logger.debug("Focus attempt executed");
    }
  };

  // Делаем несколько попыток с разными интервалами
  focusInput();
  setTimeout(focusInput, 50);
  setTimeout(focusInput, 150);
};

const handleInput = (): void => {
  try {
    const sanitizedQuery = sanitizeSearchQuery(searchQuery.value);

    if (sanitizedQuery !== searchQuery.value) {
      searchQuery.value = sanitizedQuery;
    }

    emit("update:modelValue", sanitizedQuery);

    if (sanitizedQuery.length >= 3) {
      emit("search", sanitizedQuery);
    }
  } catch (error) {
    logger.error("Error handling search input", { error });
  }
};

const clearSearch = (): void => {
  try {
    searchQuery.value = "";
    isSearchActive.value = false;
    emit("update:modelValue", "");
    emit("search", "");
    emit("searchStateChange", false);
    emit("clear");
  } catch (error) {
    logger.error("Error clearing search", { error });
  }
};

const blur = (): void => {
  searchInput.value?.blur();
};

watch(
  () => props.modelValue,
  (newValue: string) => {
    searchQuery.value = newValue;
  },
);

defineExpose({
  blur,
  focus: () => searchInput.value?.focus(),
});
</script>

<template>
  <div
    class="search-container"
    :class="{ 'is-active': isSearchActive }"
  >
    <!-- Кнопка активации поиска -->
    <button
      v-if="!isSearchActive"
      class="search-trigger"
      @click="activateSearch"
      aria-label="Активировать поиск"
    >
      <SearchIcon />
    </button>

    <!-- Поле поиска -->
    <div
      v-else
      class="search-field"
    >
      <input
        :class="{ error: showNoProducts }"
        ref="searchInput"
        v-model="searchQuery"
        type="text"
        placeholder="Поиск товаров..."
        @input="handleInput"
      />
      <button
        class="clear-search"
        @click="clearSearch"
        aria-label="Очистить поиск"
      >
        <CloseIcon />
      </button>
    </div>

    <!-- Сообщение об отсутствии товара -->
    <div
      v-if="showNoProducts"
      class="no-products-message"
    >
      <CartIcon class="no-products-icon" />
      <p class="no-products-text">Данного товара еще нет в нашем магазине!</p>
      <button
        class="try-again-button"
        @click="clearSearch"
      >
        ВЫБРАТЬ ДРУГОЙ ПРОДУКТ
      </button>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/search.css";
</style>
