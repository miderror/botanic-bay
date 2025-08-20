<script setup lang="ts">
import { useImageUrl } from "@/composables/useImageUrl";
import type { IOrder } from "@/types/order";
import { formatPrice } from "@/utils/formatters";

defineProps<{
  order: IOrder | null;
}>();

defineEmits<{
  (e: "close"): void;
}>();

const { getImageUrl, handleImageError } = useImageUrl();

const formatDate = (date?: string) => {
  if (!date) return "";
  return new Date(date).toLocaleString("ru-RU", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

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

const formatDeliveryMethod = (method: string): string => {
  const methods: Record<string, string> = {
    courier: "Курьер",
    pickup: "Самовывоз",
  };
  return methods[method] || method;
};

const getStatusClass = (status: string): string => {
  return `admin-status-${status}`;
};
</script>

<template>
  <div
    class="admin-modal-overlay"
    @click.self="$emit('close')"
  >
    <div class="admin-modal-content">
      <div class="admin-modal-header">
        <h2 class="admin-modal-title">Детали заказа</h2>
        <button
          class="admin-modal-close-btn"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div class="admin-modal-body">
        <!-- Основная информация -->
        <div class="admin-details-section">
          <h3 class="admin-details-title">Основная информация</h3>
          <div class="admin-details-grid">
            <div class="admin-details-item">
              <span class="admin-details-label">ID заказа:</span>
              <span class="admin-details-value">{{ order?.id }}</span>
            </div>
            <div class="admin-details-item">
              <span class="admin-details-label">Дата создания:</span>
              <span class="admin-details-value">{{ formatDate(order?.created_at) }}</span>
            </div>
            <div class="admin-details-item">
              <span class="admin-details-label">Статус:</span>
              <span
                class="admin-status-badge"
                :class="getStatusClass(order?.status || '')"
              >
                {{ formatStatus(order?.status || "") }}
              </span>
            </div>
            <div class="admin-details-item">
              <span class="admin-details-label">Обновлен:</span>
              <span class="admin-details-value">{{ formatDate(order?.updated_at) }}</span>
            </div>
          </div>
        </div>

        <!-- Информация о клиенте -->
        <div class="admin-details-section">
          <h3 class="admin-details-title">Информация о клиенте</h3>
          <div class="admin-details-grid">
            <div class="admin-details-item">
              <span class="admin-details-label">Имя:</span>
              <span class="admin-details-value">{{ order?.user?.full_name || "Не указано" }}</span>
            </div>
            <div class="admin-details-item">
              <span class="admin-details-label">Telegram:</span>
              <span class="admin-details-value">{{
                order?.user?.username ? "@" + order.user.username : "Не указано"
              }}</span>
            </div>
          </div>
        </div>

        <!-- Информация о доставке -->
        <div class="admin-details-section">
          <h3 class="admin-details-title">Информация о доставке</h3>
          <div class="admin-details-grid">
            <div class="admin-details-item">
              <span class="admin-details-label">Способ доставки:</span>
              <span class="admin-details-value">{{
                formatDeliveryMethod(order?.delivery_method || "")
              }}</span>
            </div>
            <div class="admin-details-item">
              <span class="admin-details-label">Адрес / Код ПВЗ:</span>
              <span class="admin-details-value">{{
                order?.delivery_point ?? order.delivery_to_location.address
              }}</span>
            </div>
            <div class="admin-details-item">
              <span class="admin-details-label">Стоимость доставки:</span>
              <span class="admin-details-value">{{ formatPrice(order?.delivery_cost || 0) }}</span>
            </div>
          </div>
        </div>

        <!-- Товары -->
        <div class="admin-details-section">
          <h3 class="admin-details-title">Товары</h3>
          <div class="admin-order-items">
            <div
              v-for="item in order?.items"
              :key="item.id"
              class="admin-order-item"
            >
              <img
                :src="getImageUrl(item.image_url)"
                :alt="item.product_name"
                class="admin-item-image"
                @error="handleImageError"
              />
              <div class="admin-item-info">
                <div class="admin-item-name">{{ item.product_name }}</div>
                <div class="admin-item-details">
                  <span class="admin-item-price"
                    >{{ formatPrice(item.price) }} × {{ item.quantity }} шт.</span
                  >
                  <span class="admin-item-subtotal">{{ formatPrice(item.subtotal) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Итоги -->
        <div class="admin-details-section admin-details-totals">
          <div class="admin-total-row">
            <span>Товары:</span>
            <span>{{ formatPrice(order?.subtotal || 0) }}</span>
          </div>
          <div class="admin-total-row">
            <span>Доставка:</span>
            <span>{{ formatPrice(order?.delivery_cost || 0) }}</span>
          </div>
          <div class="admin-total-row admin-total-final">
            <span>Итого:</span>
            <span>{{ formatPrice(order?.total || 0) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/admin.css";

/* Дополнительные стили */
.admin-details-section {
  margin-bottom: 24px;
  padding: 16px;
  background: var(--admin-bg);
  border-radius: var(--admin-border-radius-lg);
}

.admin-details-title {
  margin: 0 0 16px;
  font-size: 14px;
  font-family: var(--admin-font-heading);
  font-weight: 700;
  color: var(--admin-primary);
}

.admin-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 16px;
}

.admin-details-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.admin-details-label {
  color: var(--admin-gray);
  font-size: 10px;
  font-family: var(--admin-font-heading);
  font-weight: 700;
}

.admin-details-value {
  color: var(--admin-primary);
  font-size: 12px;
  font-family: var(--admin-font-body);
  font-weight: 500;
}

.admin-order-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.admin-order-item {
  display: flex;
  gap: 16px;
  padding: 12px;
  background: white;
  border-radius: var(--admin-border-radius-md);
}

.admin-item-image {
  width: 60px;
  height: 60px;
  object-fit: contain;
  border-radius: var(--admin-border-radius-md);
}

.admin-item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.admin-item-name {
  font-weight: 700;
  font-size: 12px;
  font-family: var(--admin-font-heading);
  color: var(--admin-primary);
}

.admin-item-details {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  color: var(--admin-gray);
  font-size: 10px;
  font-family: var(--admin-font-body);
}

.admin-item-subtotal {
  font-weight: 700;
  color: var(--admin-primary);
}

.admin-details-totals {
  background: white;
}

.admin-total-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  color: var(--admin-gray);
  font-size: 12px;
  font-family: var(--admin-font-body);
}

.admin-total-row.admin-total-final {
  border-top: 1px solid var(--admin-light-gray);
  margin-top: 8px;
  padding-top: 16px;
  color: var(--admin-primary);
  font-weight: 700;
  font-size: 16px;
}
</style>
