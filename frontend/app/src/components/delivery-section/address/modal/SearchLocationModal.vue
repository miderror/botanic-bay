<script setup lang="ts">
/**
 * Компонент модального окна с полем ввода для поиска адреса.
 * Поддерживает два режима:
 * - Самовывоз: поиск ближайших ПВЗ СДЭК по адресу пользователя
 * - Доставка: поиск конкретных адресов доставки
 *
 * @param {boolean} isOpen - Флаг открытия модального окна
 * @param {boolean} showButton - Флаг отображения кнопки "Продолжить"
 * @param {DeliveryMethod} deliveryMethod - Метод доставки (обязательный)
 * @param {object} userLocation - Координаты пользователя для приоритизации результатов
 */
import BaseModal from "@/components/common/BaseModal.vue";
import CdekIcon from "@/components/icons/CdekIcon.vue";
import CloseIcon from "@/components/icons/CloseIcon.vue";
import LocationIcon from "@/components/icons/LocationIcon.vue";
import { useAddressSearch } from "@/composables/useAddressSearch";
import { useDeliveryPointSearch } from "@/composables/useDeliveryPointSearch";
import type { IAddressSearchResult, IDeliveryPointSearchResult } from "@/types/cdek.ts";
import { DeliveryMethod } from "@/types/order";
import { computed, ref, watch } from "vue";

const props = withDefaults(
  defineProps<{
    isOpen: boolean;
    showButton?: boolean;
    deliveryMethod: DeliveryMethod;
    userLocation?: { latitude: number; longitude: number } | null;
  }>(),
  {
    showButton: false,
  },
);

const emit = defineEmits<{
  close: [];
  buttonClick: [];
  selectResult: [result: IAddressSearchResult | IDeliveryPointSearchResult];
}>();

const searchInput = ref("");
const selectedAddress = ref<IAddressSearchResult | IDeliveryPointSearchResult | null>(null);

// Определяем режим работы
const isPickupMode = computed(() => props.deliveryMethod === DeliveryMethod.PICKUP);

// Плейсхолдеры в зависимости от режима
const placeholder = computed(() =>
  isPickupMode.value ? "Введите адрес для поиска ПВЗ..." : "Введите адрес доставки...",
);

// Инициализируем композаблы для поиска
const addressSearch = useAddressSearch();
const deliveryPointSearch = useDeliveryPointSearch();

// Активный поиск в зависимости от режима
const activeSearch = computed(() => (isPickupMode.value ? deliveryPointSearch : addressSearch));

// Объединенные результаты поиска
const searchResults = computed(() => activeSearch.value.searchResults.value);
const isSearching = computed(() => activeSearch.value.isSearching.value);
const searchError = computed(() => activeSearch.value.searchError.value);

// Проверка можно ли продолжить (выбран адрес)
const canContinue = computed(() => selectedAddress.value !== null);

// Обработчик поиска
const handleSearch = async () => {
  const query = searchInput.value.trim();

  if (query.length < 3) {
    // Очищаем результаты если запрос слишком короткий
    addressSearch.clearResults();
    deliveryPointSearch.clearResults();
    return;
  }

  if (isPickupMode.value) {
    await deliveryPointSearch.searchDeliveryPoints(query, props.userLocation || undefined);
  } else {
    await addressSearch.searchDeliveryAddresses(query, props.userLocation || undefined);
  }
};

// Проверяет, что результат содержит все элементы адреса, необходимые для доставки
const isFullAddress = (result: IAddressSearchResult): boolean => {
  if (!result || typeof result !== "object") return false;
  return !!(result.street && result.house && result.city && result.country);
};

// Проверяет, можно ли выбрать адрес (для доставки нужен дом)
const canSelectAddress = (result: IAddressSearchResult | IDeliveryPointSearchResult): boolean => {
  if (isPickupMode.value) {
    return true; // Для ПВЗ можно выбрать любой результат
  }

  // Для доставки нужен полный адрес с домом
  return isFullAddress(result as IAddressSearchResult);
};

// Обработчик выбора результата
const selectResult = (result: IAddressSearchResult | IDeliveryPointSearchResult) => {
  if (!canSelectAddress(result)) {
    return; // Не даём выбрать неполный адрес
  }

  selectedAddress.value = result;
  searchInput.value = ""; // Очищаем поле поиска
  addressSearch.clearResults(); // Очищаем результаты поиска
  deliveryPointSearch.clearResults();

  emit("selectResult", result);
};

// Очистка поля ввода
const clearInput = () => {
  searchInput.value = "";
  addressSearch.clearResults();
  deliveryPointSearch.clearResults();
};

// Сброс выбранного адреса
const clearSelectedAddress = () => {
  selectedAddress.value = null;
};

// Обработчик кнопки "Продолжить"
const handleButtonClick = () => {
  if (canContinue.value) {
    emit("buttonClick");
  }
};

// Следим за изменениями поля ввода
watch(searchInput, handleSearch);

// Управляем состоянием при открытии/закрытии модала
watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      // При открытии всегда очищаем состояние
      selectedAddress.value = null;
      searchInput.value = "";
      addressSearch.clearResults();
      deliveryPointSearch.clearResults();
    } else {
      // При закрытии очищаем все
      addressSearch.clearResults();
      deliveryPointSearch.clearResults();
      searchInput.value = "";
    }
  },
);
</script>

<template>
  <BaseModal
    :modelValue="isOpen"
    @update:modelValue="$emit('close')"
    minimized
    :overlayBg="false"
    :closeButton="false"
    :closeOnOverlayClick="false"
  >
    <div class="modal-search-location-content">
      <div class="flex items-center relative">
        <input
          class="modal-input"
          :placeholder="placeholder"
          v-model="searchInput"
          autocomplete="off"
        />
        <CloseIcon
          class="absolute right-3 text-[#787878] cursor-pointer"
          @click="clearInput"
        />
      </div>

      <!-- Выбранный адрес -->
      <div
        v-if="selectedAddress"
        class="selected-address"
      >
        <div class="selected-address-content">
          <CdekIcon
            v-if="isPickupMode"
            class="selected-address-icon"
          />
          <LocationIcon
            v-else
            class="selected-address-icon"
          />

          <div class="selected-address-text">
            <div class="selected-address-title">{{ selectedAddress.title }}</div>
            <div
              v-if="isPickupMode && (selectedAddress as IDeliveryPointSearchResult).address"
              class="selected-address-subtitle"
            >
              {{ (selectedAddress as IDeliveryPointSearchResult).address }}
            </div>
            <div
              v-if="selectedAddress.distance_km"
              class="selected-address-distance"
            >
              {{ selectedAddress.distance_km.toFixed(1) }} км
            </div>
          </div>

          <CloseIcon
            class="selected-address-close"
            @click="clearSelectedAddress"
          />
        </div>
      </div>

      <!-- Результаты поиска -->
      <div
        v-if="searchResults.length > 0"
        class="search-results"
      >
        <div
          v-for="result in searchResults"
          :key="result.id"
          class="search-result-item"
          :class="{ 'search-result-disabled': !canSelectAddress(result) }"
          @click="selectResult(result)"
        >
          <!-- Разная иконка в зависимости от типа -->
          <CdekIcon
            v-if="isPickupMode"
            class="search-result-icon"
          />
          <LocationIcon
            v-else
            class="search-result-icon"
          />

          <div class="search-result-content">
            <div class="search-result-title">
              {{ result.title }}
            </div>
            <div
              v-if="isPickupMode && (result as IDeliveryPointSearchResult).address"
              class="search-result-subtitle"
            >
              {{ (result as IDeliveryPointSearchResult).address }}
            </div>
            <div
              v-if="result.distance_km"
              class="search-result-distance"
            >
              {{ result.distance_km.toFixed(1) }} км
            </div>
          </div>
        </div>
      </div>

      <!-- Индикатор загрузки -->
      <div
        v-else-if="isSearching"
        class="search-loading"
      >
        <div class="loading-spinner"></div>
        <span>Поиск...</span>
      </div>

      <!-- Сообщение об ошибке -->
      <div
        v-else-if="searchError"
        class="search-error"
      >
        {{ searchError }}
      </div>

      <!-- Сообщение при отсутствии результатов -->
      <div
        v-else-if="searchInput.length >= 3 && !isSearching"
        class="search-no-results"
      >
        Ничего не найдено
      </div>

      <div
        class="modal-search-location-button-container"
        v-if="showButton"
      >
        <button
          class="modal-button"
          :class="{ 'modal-button-disabled': !canContinue }"
          :disabled="!canContinue"
          @click="handleButtonClick"
        >
          ПРОДОЛЖИТЬ
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
@import "@/assets/styles/modal.css";
@import "@/assets/styles/search-location-modal.css";

/* Стили для выбранного адреса */
.selected-address {
  margin-top: 12px;
  padding: 12px;
  background-color: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.selected-address-content {
  display: flex;
  align-items: center;
}

.selected-address-icon {
  margin-right: 12px;
  flex-shrink: 0;
}

.selected-address-text {
  flex: 1;
  min-width: 0;
}

.selected-address-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 2px;
}

.selected-address-subtitle {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.selected-address-distance {
  font-size: 12px;
  color: #999;
}

.selected-address-close {
  cursor: pointer;
  color: #999;
  margin-left: 8px;
  flex-shrink: 0;
}

.selected-address-close:hover {
  color: #666;
}

/* Стили для результатов поиска */
.search-results {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-top: 8px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.search-result-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.search-result-item:hover {
  background-color: #f8f9fa;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.search-result-disabled:hover {
  background-color: transparent;
}

.search-result-icon {
  margin-right: 12px;
  flex-shrink: 0;
}

.search-result-content {
  flex: 1;
  min-width: 0;
}

.search-result-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 2px;
}

.search-result-subtitle {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.search-result-distance {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

/* Стили для состояний загрузки и ошибок */
.search-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: #666;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e0e0e0;
  border-top: 2px solid #666;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.search-error {
  padding: 16px;
  color: #d32f2f;
  text-align: center;
  font-size: 14px;
}

.search-no-results {
  padding: 16px;
  color: #666;
  text-align: center;
  font-size: 14px;
}

/* Стили для неактивной кнопки */
.modal-button-disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-button-disabled:hover {
  background-color: initial;
}
</style>
