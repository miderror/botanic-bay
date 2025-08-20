<script setup lang="ts">
import ExportOrdersButton from "@/components/admin/orders/ExportOrdersButton.vue";
import OrderDetailsModal from "@/components/admin/orders/OrderDetailsModal.vue";
import StatusChangeModal from "@/components/admin/orders/StatusChangeModal.vue";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import { useNotification } from "@/composables/useNotification";
import { ADMIN_ORDERS_PER_PAGE } from "@/config/pagination";
import { adminService } from "@/services/adminService";
import type { IOrder } from "@/types/order";
import { OrderStatus } from "@/types/order";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import { debounce } from "lodash-es";
import { onMounted, ref, watch } from "vue";

// Состояние компонента
const orders = ref<IOrder[]>([]);
const currentPage = ref(1);
const totalPages = ref(1);
const isLoading = ref(false);
const error = ref<string | null>(null);

// Состояние модальных окон
const showStatusModal = ref(false);
const showDetailsModal = ref(false);
const selectedOrder = ref<IOrder | null>(null);

// Уведомления
const { showNotification } = useNotification();

// Фильтры
const filters = ref({
  orderId: "",
  status: "",
  fromDate: "",
  toDate: "",
  minTotal: "",
  maxTotal: "",
});

// Доступные статусы заказа
const orderStatuses = Object.values(OrderStatus);

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
    pending: "Ожидает оплаты",
    paid: "Оплачен",
    processing: "В обработке",
    shipped: "Отправлен",
    delivered: "Доставлен",
    cancelled: "Отменён",
  };
  return statuses[status] || status;
};

/**
 * Возвращает человекочитаемое название способа доставки
 */
const formatDeliveryMethod = (method: string): string => {
  const methods: Record<string, string> = {
    courier: "Курьер",
    pickup: "Самовывоз",
  };
  return methods[method] || method;
};

/**
 * Возвращает CSS класс для статуса заказа
 */
const getStatusClass = (status: string): string => {
  return `admin-status-${status}`;
};

/**
 * Возвращает общее количество товаров в заказе
 */
const getItemsCount = (order: IOrder): string => {
  const count = order.items.reduce((acc, item) => acc + item.quantity, 0);
  return `${count} шт.`;
};

/**
 * Загружает список заказов с учетом текущей страницы и фильтров
 */
const loadOrders = async () => {
  try {
    isLoading.value = true;
    error.value = null;

    // Преобразуем фильтры в формат для API
    const apiFilters = {
      order_id: filters.value.orderId || undefined,
      status: filters.value.status || undefined,
      from_date: filters.value.fromDate ? new Date(filters.value.fromDate).toISOString() : undefined,
      to_date: filters.value.toDate ? new Date(filters.value.toDate + "T23:59:59").toISOString() : undefined,
      min_total: filters.value.minTotal ? Number(filters.value.minTotal) : undefined,
      max_total: filters.value.maxTotal ? Number(filters.value.maxTotal) : undefined,
    };

    const response = await adminService.getOrders(currentPage.value, ADMIN_ORDERS_PER_PAGE, apiFilters);

    orders.value = response.items;
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
const openStatusModal = (order: IOrder) => {
  selectedOrder.value = order;
  showStatusModal.value = true;
};

/**
 * Закрывает модальное окно изменения статуса заказа
 */
const closeStatusModal = () => {
  selectedOrder.value = null;
  showStatusModal.value = false;
};

/**
 * Открывает модальное окно с деталями заказа
 */
const openDetailsModal = (order: IOrder) => {
  selectedOrder.value = order;
  showDetailsModal.value = true;
};

/**
 * Закрывает модальное окно с деталями заказа
 */
const closeDetailsModal = () => {
  selectedOrder.value = null;
  showDetailsModal.value = false;
};

/**
 * Обрабатывает изменение статуса заказа
 */
const handleStatusChange = async (orderId: string, newStatus: string) => {
  try {
    await adminService.updateOrderStatus(orderId, newStatus);
    await loadOrders(); // Перезагружаем список
    showNotification("Статус заказа успешно обновлен", "success");
    closeStatusModal();
  } catch (err) {
    logger.error("Failed to update order status", {
      orderId,
      newStatus,
      error: err,
    });
    showNotification("Не удалось обновить статус заказа", "error");
  }
};

/**
 * Обрабатывает переход на другую страницу пагинации
 */
const changePage = async (newPage: number) => {
  try {
    if (newPage < 1 || newPage > totalPages.value) return;
    currentPage.value = newPage;
    await loadOrders();
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
    await loadOrders();
  } catch (err) {
    logger.error("Failed to apply filters", { error: err });
    showNotification("Не удалось применить фильтры", "error");
  }
}, 300);

// Наблюдатель только за изменениями фильтров
watch(
  [
    () => filters.value.orderId,
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
  loadOrders();
});
</script>

<template>
  <div class="admin-orders">
    <div class="admin-header">
      <h1>Управление заказами</h1>
      <div class="admin-header-actions">
        <ExportOrdersButton :currentFilters="filters" />
      </div>
    </div>

    <!-- Фильтры -->
    <div class="admin-filters">
      <!-- Поиск по ID -->
      <div class="admin-filter-group">
        <input
          v-model="filters.orderId"
          type="text"
          placeholder="ID заказа"
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
            v-for="status in orderStatuses"
            :key="status"
            :value="status"
          >
            {{ formatStatus(status) }}
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

      <!-- Фильтр по сумме -->
      <div class="admin-filter-group">
        <input
          v-model="filters.minTotal"
          type="number"
          class="admin-filter-input"
          placeholder="Сумма от"
          @input="handleFilterChange"
        />
        <input
          v-model="filters.maxTotal"
          type="number"
          class="admin-filter-input"
          placeholder="Сумма до"
          @input="handleFilterChange"
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

      <template v-else-if="orders.length === 0">
        <div class="admin-empty-state">
          <p>Заказы не найдены</p>
        </div>
      </template>

      <template v-else>
        <table class="admin-table">
          <thead>
            <tr>
              <th>ID заказа</th>
              <th>Дата создания</th>
              <th>Покупатель</th>
              <th>Товары</th>
              <th>Способ доставки</th>
              <th>Сумма</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="order in orders"
              :key="order.id"
            >
              <td>{{ order.id }}</td>
              <td>{{ formatDate(order.created_at) }}</td>
              <td>{{ order.user?.full_name || "Не указано" }}</td>
              <td>{{ getItemsCount(order) }}</td>
              <td>{{ formatDeliveryMethod(order.delivery_method) }}</td>
              <td>{{ formatPrice(order.total) }}</td>
              <td>
                <span
                  class="admin-status-badge"
                  :class="getStatusClass(order.status)"
                >
                  {{ formatStatus(order.status) }}
                </span>
              </td>
              <td class="admin-actions">
                <button
                  class="admin-action-btn edit"
                  @click="openStatusModal(order)"
                >
                  Изменить статус
                </button>
                <button
                  class="admin-action-btn details"
                  @click="openDetailsModal(order)"
                >
                  Детали
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
      :order="selectedOrder"
      @close="closeStatusModal"
      @save="handleStatusChange"
    />

    <OrderDetailsModal
      v-if="showDetailsModal"
      :order="selectedOrder"
      @close="closeDetailsModal"
    />
  </div>
</template>

<style>
@import "@/assets/styles/admin.css";
</style>
