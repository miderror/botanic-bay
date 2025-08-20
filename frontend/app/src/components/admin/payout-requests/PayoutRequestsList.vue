<script setup lang="ts">
import StatusChangeModal from "@/components/admin/payout-requests/StatusChangeModal.vue";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import { useNotification } from "@/composables/useNotification";
import { ADMIN_PAYOUTS_PER_PAGE } from "@/config/pagination";
import { adminService } from "@/services/adminService";
import { type IReferralPayoutRequest, ReferralPayoutStatus } from "@/types/business.ts";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import { debounce } from "lodash-es";
import { onMounted, ref, watch } from "vue";

// Состояние компонента
const payouts = ref<IReferralPayoutRequest[]>([]);
const currentPage = ref(1);
const totalPages = ref(1);
const isLoading = ref(false);
const error = ref<string | null>(null);

// Состояние модальных окон
const showStatusModal = ref(false);
const selectedPayout = ref<IReferralPayoutRequest | null>(null);

// Уведомления
const { showNotification } = useNotification();

// Фильтры
const filters = ref({
  payoutId: "",
  status: "pending",
  fromDate: "",
  toDate: "",
  minTotal: "",
  maxTotal: "",
});

// Доступные статусы заказа
const payoutStatuses = Object.values(ReferralPayoutStatus);

/**
 * Форматирует дату в локальном формате
 */
const formatDate = (date: string) => {
  return new Date(date).toLocaleString("ru-RU", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

/**
 * Возвращает человекочитаемое название статуса заказа
 */
const formatStatus = (status: string): string => {
  const statuses: Record<string, string> = {
    pending: "Ожидает решения",
    approved: "Одобрено",
    rejected: "Отклонено",
  };
  return statuses[status] || status;
};

/**
 * Возвращает CSS класс для статуса заказа
 */
const getStatusClass = (status: string): string => {
  return `admin-status-${status}`;
};

/**
 * Загружает список заказов с учетом текущей страницы и фильтров
 */
const loadPayouts = async () => {
  try {
    isLoading.value = true;
    error.value = null;

    // Преобразуем фильтры в формат для API
    const apiFilters = {
      id: filters.value.payoutId || undefined,
      status: filters.value.status || undefined,
      fromDate: filters.value.fromDate ? new Date(filters.value.fromDate).toISOString() : undefined,
      toDate: filters.value.toDate ? new Date(filters.value.toDate + "T23:59:59").toISOString() : undefined,
    };

    const response = await adminService.getPayoutRequests(
      currentPage.value,
      ADMIN_PAYOUTS_PER_PAGE,
      apiFilters,
    );

    payouts.value = response.items;
    totalPages.value = response.pages;

    logger.info("Orders loaded for admin", {
      page: currentPage.value,
      total: response.total,
      filters: apiFilters,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to load orders";
    error.value = message;
    logger.error("Failed to load orders", { error: err });
    showNotification("Не удалось загрузить список заказов", "error");
  } finally {
    isLoading.value = false;
  }
};

/**
 * Открывает модальное окно изменения статуса заказа
 */
const openStatusModal = (order: IReferralPayoutRequest) => {
  selectedPayout.value = order;
  showStatusModal.value = true;
};

/**
 * Закрывает модальное окно изменения статуса заказа
 */
const closeStatusModal = () => {
  selectedPayout.value = null;
  showStatusModal.value = false;
};

/**
 * Обрабатывает изменение статуса заказа
 */
const handleStatusChange = async (id: string, newStatus: string) => {
  try {
    await adminService.updatePayoutStatus(id, newStatus);
    await loadPayouts(); // Перезагружаем список
    showNotification("Статус заявки успешно обновлен", "success");
    closeStatusModal();
  } catch (err) {
    logger.error("Failed to update payout request status", {
      id,
      newStatus,
      error: err,
    });
    showNotification("Не удалось обновить статус заявки", "error");
  }
};

/**
 * Обрабатывает переход на другую страницу пагинации
 */
const changePage = async (newPage: number) => {
  try {
    if (newPage < 1 || newPage > totalPages.value) return;
    currentPage.value = newPage;
    await loadPayouts();
  } catch (err) {
    logger.error("Failed to change page", { error: err });
    showNotification("Не удалось загрузить страницу", "error");
  }
};

/**
 * Обрабатывает изменение фильтров с debounce
 */
const handleFilterChange = debounce(async () => {
  try {
    currentPage.value = 1; // Сбрасываем страницу при изменении фильтров
    await loadPayouts();
  } catch (err) {
    logger.error("Failed to apply filters", { error: err });
    showNotification("Не удалось применить фильтры", "error");
  }
}, 300);

// Наблюдатель только за изменениями фильтров
watch(
  [
    () => filters.value.payoutId,
    () => filters.value.status,
    () => filters.value.fromDate,
    () => filters.value.toDate,
    () => filters.value.minTotal,
    () => filters.value.maxTotal,
  ],
  debounce(() => {
    // Используем handleFilterChange для обработки изменений фильтров
    handleFilterChange();
  }, 300),
);

// Инициализация компонента
onMounted(() => {
  loadPayouts();
});
</script>

<template>
  <div class="admin-payout-requests">
    <div class="admin-header">
      <h1>Управление заявками на вывод</h1>
    </div>

    <!-- Фильтры -->
    <div class="admin-filters">
      <!-- Поиск по ID -->
      <div class="admin-filter-group">
        <input
          v-model="filters.payoutId"
          type="text"
          placeholder="ID заявки"
          class="admin-filter-input"
          @input="handleFilterChange"
        />

        <!-- Фильтр по статусу -->
        <select
          v-model="filters.status"
          class="admin-filter-select"
          @change="handleFilterChange"
        >
          <option value="">Все статусы</option>
          <option
            v-for="status in payoutStatuses"
            :key="status"
            :value="status"
          >
            {{ formatStatus(status.toLowerCase()) }}
          </option>
        </select>
      </div>

      <!-- Фильтр по дате -->
      <div class="admin-filter-group">
        <input
          v-model="filters.fromDate"
          type="date"
          class="admin-filter-input"
          placeholder="Дата от"
          @change="handleFilterChange"
        />
        <input
          v-model="filters.toDate"
          type="date"
          class="admin-filter-input"
          placeholder="Дата до"
          @change="handleFilterChange"
        />
      </div>
    </div>

    <!-- Таблица заказов -->
    <div class="admin-table-container">
      <template v-if="isLoading">
        <LoadingSpinner />
      </template>

      <template v-else-if="error">
        <div class="admin-empty-state">
          <p>{{ error }}</p>
        </div>
      </template>

      <template v-else-if="payouts.length === 0">
        <div class="admin-empty-state">
          <p>Заявки не найдены</p>
        </div>
      </template>

      <template v-else>
        <table class="admin-table">
          <thead>
            <tr>
              <th>ID заявки</th>
              <th>Дата создания</th>
              <th>Пользователь</th>
              <th>Сумма</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="payout in payouts"
              :key="payout.id"
            >
              <td>{{ payout.id }}</td>
              <td>{{ formatDate(payout.created_at) }}</td>
              <td>{{ payout.referrer?.full_name || "Не указано" }}</td>
              <td>{{ formatPrice(payout.amount) }}</td>
              <td>
                <span
                  class="admin-status-badge"
                  :class="getStatusClass(payout.status.toLowerCase())"
                >
                  {{ formatStatus(payout.status?.toLowerCase()) }}
                </span>
              </td>
              <td class="admin-actions">
                <button
                  class="admin-action-btn approve"
                  @click="openStatusModal(payout)"
                >
                  Изменить
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </template>
    </div>

    <!-- Пагинация -->
    <div class="admin-pagination">
      <button
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
        class="admin-page-btn"
      >
        ←
      </button>
      <span class="admin-page-info"> Страница {{ currentPage }} из {{ totalPages }} </span>
      <button
        :disabled="currentPage === totalPages"
        @click="changePage(currentPage + 1)"
        class="admin-page-btn"
      >
        →
      </button>
    </div>

    <!-- Модальные окна -->
    <StatusChangeModal
      v-if="showStatusModal"
      :payout="selectedPayout"
      @close="closeStatusModal"
      @save="handleStatusChange"
    />
  </div>
</template>

<style>
@import "@/assets/styles/admin.css";
</style>
