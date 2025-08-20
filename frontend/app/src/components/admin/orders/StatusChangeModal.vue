<script setup lang="ts">
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import type { IOrder } from "@/types/order";
import { logger } from "@/utils/logger";
import { computed, ref, watch } from "vue";

const props = defineProps<{
  order: IOrder | null;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", orderId: string, status: string, comment?: string): void;
}>();

const isLoading = ref(false);
const selectedStatus = ref("");
const comment = ref("");

// Определяем доступные статусы в зависимости от текущего
const availableStatuses = computed(() => {
  if (!props.order) return [];

  const currentStatus = props.order.status;

  // Обновляем правила перехода статусов с учетом всех возможных переходов
  const transitionRules: Record<string, string[]> = {
    pending: ["paid", "processing", "cancelled"], // Добавляем 'processing'
    paid: ["processing", "shipped", "cancelled"], // Добавляем 'shipped'
    processing: ["shipped", "cancelled"],
    shipped: ["delivered", "cancelled"],
    delivered: [], // Конечный статус
    cancelled: [], // Конечный статус
  };

  return transitionRules[currentStatus] || [];
});

const canSubmit = computed(() => {
  return selectedStatus.value && selectedStatus.value !== props.order?.status;
});

// Методы форматирования из общих утилит
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

const getStatusClass = (status: string): string => {
  return `admin-status-${status}`;
};

const handleSubmit = async () => {
  if (!props.order || !canSubmit.value) return;

  try {
    isLoading.value = true;
    await emit("save", props.order.id, selectedStatus.value, comment.value);
  } catch (error) {
    logger.error("Failed to update order status", {
      orderId: props.order.id,
      newStatus: selectedStatus.value,
      error,
    });
  } finally {
    isLoading.value = false;
  }
};

// При открытии модального окна устанавливаем текущий статус
watch(
  () => props.order,
  (newOrder) => {
    if (newOrder) {
      selectedStatus.value = newOrder.status;
      comment.value = "";
    }
  },
);
</script>

<template>
  <div class="admin-modal-overlay">
    <div class="admin-modal-content">
      <div class="admin-modal-header">
        <h2 class="admin-modal-title">Изменение статуса заказа</h2>
        <button
          class="admin-modal-close-btn"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div class="admin-modal-body">
        <!-- Информация о заказе -->
        <div class="admin-form-group">
          <div class="admin-info-row">
            <span class="admin-form-label">ID заказа:</span>
            <span class="admin-info-value">{{ order?.id }}</span>
          </div>
          <div class="admin-info-row">
            <span class="admin-form-label">Текущий статус:</span>
            <span
              class="admin-status-badge"
              :class="getStatusClass(order?.status || '')"
            >
              {{ formatStatus(order?.status || "") }}
            </span>
          </div>
        </div>

        <!-- Выбор нового статуса -->
        <div class="admin-form-group">
          <label class="admin-form-label">Новый статус:</label>
          <select
            v-model="selectedStatus"
            class="admin-form-select"
          >
            <option
              v-for="status in availableStatuses"
              :key="status"
              :value="status"
            >
              {{ formatStatus(status) }}
            </option>
          </select>
        </div>

        <!-- Комментарий к изменению -->
        <div class="admin-form-group">
          <label class="admin-form-label">Комментарий (опционально):</label>
          <textarea
            v-model="comment"
            class="admin-form-textarea"
            rows="3"
            placeholder="Причина изменения статуса"
          ></textarea>
        </div>

        <!-- Кнопки действий -->
        <div class="admin-form-actions">
          <button
            class="admin-btn admin-btn-cancel"
            @click="$emit('close')"
            :disabled="isLoading"
          >
            Отмена
          </button>
          <button
            class="admin-btn admin-btn-primary"
            @click="handleSubmit"
            :disabled="isLoading || !canSubmit"
          >
            <LoadingSpinner
              v-if="isLoading"
              small
            />
            <span v-else>Сохранить</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/admin.css";
</style>
