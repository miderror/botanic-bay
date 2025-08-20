<script setup lang="ts">
import { useNotification } from "@/composables/useNotification";
import { adminService } from "@/services/adminService";
import type { IAdminOrderFilter } from "@/types/admin";
import { ExportFormat } from "@/types/admin";
import { logger } from "@/utils/logger";
import { ref } from "vue";

const props = defineProps<{
  currentFilters?: IAdminOrderFilter;
}>();

// Состояние компонента
const showModal = ref(false);
const exportFormat = ref(ExportFormat.EXCEL);
const useCurrentFilters = ref(true);
const isExporting = ref(false);
const errorMessage = ref("");
const { showNotification } = useNotification();

// Методы
const showExportModal = () => {
  showModal.value = true;
  errorMessage.value = "";
};

const closeModal = () => {
  if (isExporting.value) return;
  showModal.value = false;
};

const exportOrders = async () => {
  try {
    isExporting.value = true;
    errorMessage.value = "";

    // Определяем фильтры для экспорта
    const filters = useCurrentFilters.value ? props.currentFilters : undefined;

    logger.info("Starting orders export via Telegram", {
      format: exportFormat.value,
      useFilters: useCurrentFilters.value,
      filters,
    });

    // Всегда экспортируем через Telegram бота
    await exportViaTelegram(filters);
  } catch (error) {
    logger.error("Export failed", { error });
    errorMessage.value = "Не удалось экспортировать данные. Пожалуйста, попробуйте позже.";
    showNotification("Ошибка при экспорте данных", "error");
  } finally {
    isExporting.value = false;
  }
};

// Экспорт через Telegram бота
const exportViaTelegram = async (filters?: IAdminOrderFilter) => {
  try {
    // Проверяем доступность Telegram WebApp
    if (!window.Telegram?.WebApp?.initDataUnsafe?.user?.id) {
      throw new Error("Telegram WebApp не доступен или нет данных пользователя");
    }

    // Вызываем сервис для экспорта через Telegram
    const result = await adminService.exportOrdersToTelegram(exportFormat.value, filters);

    if (result.success) {
      showNotification("Файл будет отправлен вам в личном сообщении бота", "success");
      closeModal();
    } else {
      throw new Error(result.message || "Не удалось отправить файл через Telegram");
    }
  } catch (error) {
    logger.error("Telegram export failed", { error });
    throw error;
  }
};
</script>

<template>
  <div class="admin-header-actions">
    <button
      @click="showExportModal"
      class="admin-action-btn export"
    >
      <span>Экспорт</span>
    </button>

    <!-- Модальное окно для выбора формата экспорта -->
    <div
      v-if="showModal"
      class="admin-modal-overlay"
      @click.self="closeModal"
    >
      <div class="admin-modal-content">
        <div class="admin-modal-header">
          <h2 class="admin-modal-title">Экспорт заказов</h2>
          <button
            class="admin-modal-close-btn"
            @click="closeModal"
          >
            ✕
          </button>
        </div>

        <div class="admin-modal-body">
          <div class="admin-form-group">
            <label class="admin-form-label">Формат экспорта</label>
            <div class="admin-radio-group">
              <label class="admin-radio-label">
                <input
                  type="radio"
                  v-model="exportFormat"
                  :value="ExportFormat.CSV"
                  class="admin-radio"
                />
                <span class="admin-radio-text">CSV</span>
              </label>
              <label class="admin-radio-label admin-radio-label-margin">
                <input
                  type="radio"
                  v-model="exportFormat"
                  :value="ExportFormat.EXCEL"
                  class="admin-radio"
                />
                <span class="admin-radio-text">Excel</span>
              </label>
            </div>
          </div>

          <div class="admin-form-group">
            <label class="admin-form-label">Применить текущие фильтры</label>
            <label class="admin-checkbox-label">
              <input
                type="checkbox"
                v-model="useCurrentFilters"
                class="admin-checkbox"
              />
              <span>Использовать активные фильтры</span>
            </label>
          </div>

          <div
            v-if="errorMessage"
            class="admin-error-message"
          >
            {{ errorMessage }}
          </div>

          <div class="admin-form-actions">
            <button
              class="admin-btn admin-btn-cancel"
              @click="closeModal"
              :disabled="isExporting"
            >
              Отмена
            </button>
            <button
              class="admin-btn admin-btn-primary admin-btn-with-loader"
              @click="exportOrders"
              :disabled="isExporting"
            >
              <span
                v-if="isExporting"
                class="admin-btn-loading-indicator"
              ></span>
              <span :class="{ 'loader-text-spacing': isExporting }">Экспортировать</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* Используем классы из глобальных стилей admin.css */
.admin-radio-text {
  font-family: var(--admin-font-body);
  font-size: 12px;
  color: var(--admin-primary);
  font-weight: 700;
  padding-left: 5px;
}

.admin-radio-label {
  margin-right: 20px;
}

.admin-btn-with-loader {
  position: relative;
  padding-left: 45px;
}

.admin-btn-loading-indicator {
  position: absolute;
  left: 20px;
  top: 50%;
  margin-top: -6px;
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
}

.loader-text-spacing {
  margin-left: 10px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
