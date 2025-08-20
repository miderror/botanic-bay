<script setup lang="ts">
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import { type IReferralPayoutRequest, ReferralPayoutStatus } from "@/types/business.ts";
import { formatPrice } from "@/utils/formatters.ts";
import { logger } from "@/utils/logger";
import { computed, ref, watch } from "vue";

const props = defineProps<{
  payout: IReferralPayoutRequest | null;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", id: string, status: string): void;
}>();

const isLoading = ref(false);
const selectedStatus = ref<ReferralPayoutStatus | null>(null);

// Определяем доступные статусы в зависимости от текущего
const availableStatuses = computed(() => {
  if (!props.payout) return [];

  const currentStatus = props.payout.status ?? ReferralPayoutStatus.PENDING;

  // Обновляем правила перехода статусов с учетом всех возможных переходов
  const transitionRules: Record<string, string[]> = {
    pending: ["approved", "rejected"],
    rejected: ["approved"],
    approved: ["rejected"],
  };

  return transitionRules[currentStatus] || [];
});

const canSubmit = computed(() => {
  return selectedStatus.value && selectedStatus.value !== props.payout?.status;
});

const copyData = (data: object) => {
  navigator.clipboard.writeText(data.toString());
};

// Методы форматирования из общих утилит
const formatStatus = (status: string): string => {
  const statuses: Record<string, string> = {
    pending: "Ожидает решения",
    approved: "Одобрено",
    rejected: "Отклонено",
  };
  return statuses[status] || status;
};

const getStatusClass = (status: string): string => {
  return `admin-status-${status}`;
};

const handleSubmit = async () => {
  if (!props.payout || !canSubmit.value) return;

  try {
    isLoading.value = true;
    await emit("save", props.payout.id, selectedStatus.value);
  } catch (error) {
    logger.error("Failed to update payout request status", {
      payoutId: props.payout.id,
      newStatus: selectedStatus.value,
      error,
    });
  } finally {
    isLoading.value = false;
  }
};

// При открытии модального окна устанавливаем текущий статус
watch(
  () => props.payout,
  (payout) => {
    if (payout) {
      selectedStatus.value = payout.status;
    }
  },
);
</script>

<template>
  <div class="admin-modal-overlay">
    <div class="admin-modal-content">
      <div class="admin-modal-header">
        <h2 class="admin-modal-title">Изменение статуса заявки</h2>
        <button
          class="admin-modal-close-btn"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div class="admin-modal-body">
        <div class="admin-form-group">
          <div class="admin-info-row">
            <span class="admin-form-label">ID заявки:</span>
            <span
              class="admin-info-value copyable"
              @click="copyData(payout?.id)"
              >{{ payout?.id }}</span
            >
          </div>
          <div class="admin-info-row">
            <span class="admin-form-label">БИК/SWIFT:</span>
            <span
              class="admin-info-value copyable"
              @click="copyData(payout?.bank_code)"
              >{{ payout?.bank_code }}</span
            >
          </div>
          <div class="admin-info-row">
            <span class="admin-form-label">Счет/IBAN:</span>
            <span
              class="admin-info-value copyable"
              @click="copyData(payout?.account_number)"
              >{{ payout?.account_number }}</span
            >
          </div>
          <div class="admin-info-row">
            <span class="admin-form-label">Сумма:</span>
            <span
              class="admin-info-value copyable"
              @click="copyData(payout?.amount)"
              >{{ formatPrice(payout?.amount) }}</span
            >
          </div>
          <div class="admin-info-row">
            <span class="admin-form-label">Текущий статус:</span>
            <span
              class="admin-status-badge"
              :class="getStatusClass(payout?.status || '')"
            >
              {{ formatStatus(payout?.status.toLowerCase() || "") }}
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
              {{ formatStatus(status.toLowerCase()) }}
            </option>
          </select>
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
