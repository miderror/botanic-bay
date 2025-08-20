<script setup lang="ts">
/**
 * Компонент для отображения панели поиска приглашенного пользователя.
 * При активации поиска отображает поле ввода и кнопку очистки.
 */
import CartIcon from "@/components/icons/CartIcon.vue";
import CloseIcon from "@/components/icons/CloseSearchIcon.vue";
import SearchIcon from "@/components/icons/SearchIcon.vue";
import { logger } from "@/utils/logger";
import { sanitizeSearchQuery } from "@/utils/sanitizer";
import { nextTick, ref, watch } from "vue";

const isSearchActive = ref(false);
const searchQuery = ref<string>("");

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
        placeholder="Найти пользователя..."
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

    <!-- Сообщение об отсутствии результатов -->
    <div
      v-if="showNoProducts"
      class="no-products-message"
    >
      <CartIcon class="no-products-icon" />
      <p class="no-products-text">По вашему запросу ничего не найдено!</p>
      <button
        class="try-again-button"
        @click="clearSearch"
      >
        НАЙТИ ДРУГОГО ПОЛЬЗОВАТЕЛЯ
      </button>
    </div>
  </div>
</template>

<style>
/* Контейнер поиска */
.search-container {
  position: relative;
  height: 40px;
  display: flex;
  align-items: center;
}

/* Кнопка активации поиска */
.search-trigger {
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.search-trigger:hover {
  opacity: 0.8;
}

/* Поле поиска */
.search-field {
  width: 360px;
  height: 34px;
  position: relative;
  display: flex;
  align-items: center;
}

.search-field input {
  width: 100%;
  height: 100%;
  padding: 18px 40px 18px 26px; /* Увеличиваем правый padding */
  background: #f0f0f0;
  box-shadow: 0px 1px 1px #c5c4c4 inset;
  border-radius: 100px;
  border: none;
  color: #252525;
  font-size: 10px;
  font-family: var(--font-open-sans-hebrew);
  font-weight: 700;
  line-height: 10px;
}

.search-field input.error {
  text-align: left;
  border: 2px solid #ff5b5b;
  color: #ff5b5b;
  margin: 0;
}

.search-field input:focus {
  outline: none;
}

.search-field input::placeholder {
  color: #787878;
}

/* Кнопка очистки */
.clear-search {
  position: absolute;
  right: 0; /* Прижимаем к правому краю поля ввода */
  padding: 0px; /* Одинаковые отступы со всех сторон */
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Сообщение об отсутствии товара */
.no-products-message {
  position: absolute;
  top: 112px;
  left: 50%;
  transform: translateX(-50%);
  width: 276px;
  padding: 32px 0;
  background: rgba(240, 240, 240, 0.4);
  backdrop-filter: blur(4px);
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 22px;
  z-index: 10;
}

.no-products-icon {
  width: 37px;
  height: 37px;
  color: #252525;
}

.no-products-text {
  color: #252525;
  font-size: 14px;
  font-family: var(--font-open-sans-hebrew);
  font-weight: 700;
  line-height: 16.38px;
  text-align: center;
  width: 173px;
}

/* Кнопка "Выбрать другой продукт" */
.try-again-button {
  padding: 10px 30px;
  background: #252525;
  border-radius: 100px;
  border: none;
  color: white;
  font-size: 12px;
  font-family: var(--font-inter);
  font-weight: 700;
  line-height: 14.53px;
  letter-spacing: 0.12px;
  text-transform: uppercase;
  cursor: pointer;
  transition: opacity 0.2s;
}

.try-again-button:hover {
  opacity: 0.9;
}

/* Анимации */
.search-field,
.no-products-message {
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
