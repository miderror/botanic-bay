<script setup lang="ts">
import type { IOrderStats } from "@/types/admin";
import { formatPrice } from "@/utils/formatters";

defineProps<{
  stats: IOrderStats;
}>();

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
</script>

<template>
  <div class="admin-stats">
    <div class="admin-stat-card">
      <h3>Всего заказов</h3>
      <div class="admin-stat-value">{{ stats.total_count }}</div>
    </div>
    <div class="admin-stat-card">
      <h3>Общая выручка</h3>
      <div class="admin-stat-value">{{ formatPrice(stats.total_revenue) }}</div>
    </div>
    <div class="admin-stat-card">
      <h3>Средний чек</h3>
      <div class="admin-stat-value">{{ formatPrice(stats.average_order_value) }}</div>
    </div>
    <div class="admin-stat-card">
      <h3>По статусам</h3>
      <div class="admin-status-list">
        <div
          v-for="(count, status) in stats.status_counts"
          :key="status"
          class="admin-status-item"
        >
          <span
            class="admin-status-badge"
            :class="getStatusClass(status)"
          >
            {{ formatStatus(status) }}
          </span>
          <span class="admin-status-count">{{ count }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/admin.css";

/* Специфичные стили */
.admin-status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.admin-status-count {
  font-weight: 700;
  font-size: 14px;
  color: var(--admin-primary);
}
</style>
