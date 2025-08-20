<script setup lang="ts">
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import { useImageUrl } from "@/composables/useImageUrl";
import { useNotification } from "@/composables/useNotification";
import { useOrderFormatting } from "@/composables/useOrderFormatting";
import { orderService } from "@/services/orderService";
import type { IOrder } from "@/types/order";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const props = defineProps<{
  id: string;
}>();

const router = useRouter();
const { showNotification } = useNotification();
const { getImageUrl, handleImageError } = useImageUrl();
const { formatDate, formatStatus, getStatusClass, formatDeliveryMethod, canBeCancelled } =
  useOrderFormatting();

const order = ref<IOrder | null>(null);
const error = ref<string | null>(null);

const loadOrder = async () => {
  try {
    order.value = await orderService.getOrderDetails(props.id);
    logger.info("Order details loaded", { orderId: props.id });
  } catch (err) {
    error.value = "Не удалось загрузить информацию о заказе";
    logger.error("Failed to load order details", {
      orderId: props.id,
      error: err,
    });
  }
};

const handleCancel = async () => {
  try {
    await orderService.cancelOrder(props.id);
    await loadOrder(); // Перезагружаем заказ
    showNotification("Заказ успешно отменен", "success");
    logger.info("Order cancelled", { orderId: props.id });
  } catch (err) {
    showNotification("Не удалось отменить заказ", "error");
    logger.error("Failed to cancel order", {
      orderId: props.id,
      error: err,
    });
  }
};

onMounted(() => {
  loadOrder();
});
</script>

<template>
  <div
    class="order-details"
    v-if="order"
  >
    <div class="order-header">
      <h2>Заказ от {{ formatDate(order.created_at) }}</h2>
      <div
        class="order-status"
        :class="getStatusClass(order.status)"
      >
        {{ formatStatus(order.status) }}
      </div>
    </div>

    <div class="order-section">
      <h3>Товары</h3>
      <div class="order-items">
        <div
          v-for="item in order.items"
          :key="item.id"
          class="order-item"
        >
          <img
            :src="getImageUrl(item.image_url)"
            :alt="item.product_name"
            @error="handleImageError"
            class="item-image"
          />
          <div class="item-info">
            <div class="item-name">{{ item.product_name }}</div>
            <div class="item-details">
              <div class="item-price">{{ formatPrice(item.price) }} × {{ item.quantity }} шт.</div>
              <div class="item-subtotal">{{ formatPrice(item.subtotal) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="order-section">
      <h3>Доставка</h3>
      <div class="delivery-info">
        <div class="delivery-method">{{ formatDeliveryMethod(order.delivery_method) }}</div>
        <div class="delivery-address">
          {{ order?.delivery_point ?? order?.delivery_to_location.address }}
        </div>
        <div class="delivery-cost">Стоимость доставки: {{ formatPrice(order.delivery_cost) }}</div>
      </div>
    </div>

    <div class="order-total">
      <div class="total-row">
        <span>Товары:</span>
        <span>{{ formatPrice(order.subtotal) }}</span>
      </div>
      <div class="total-row">
        <span>Доставка:</span>
        <span>{{ formatPrice(order.delivery_cost) }}</span>
      </div>
      <div class="total-row final">
        <span>Итого:</span>
        <span>{{ formatPrice(order.total) }}</span>
      </div>
    </div>

    <div
      class="order-actions"
      v-if="canBeCancelled(order.status)"
    >
      <button
        class="cancel-button"
        @click="handleCancel"
      >
        Отменить заказ
      </button>
    </div>
  </div>

  <div
    v-else-if="error"
    class="error-state"
  >
    <p>{{ error }}</p>
    <button
      class="back-button"
      @click="router.push('/orders')"
    >
      Вернуться к заказам
    </button>
  </div>

  <LoadingSpinner v-else />
</template>

<style scoped>
.order-details {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.order-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #252525;
  margin: 0;
}

.order-status {
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.status-pending {
  background: #fff3e0;
  color: #f4b942;
}

.status-paid {
  background: #e8f5e9;
  color: #66ca1a;
}

.status-processing {
  background: #e3f2fd;
  color: #2196f3;
}

.status-shipped {
  background: #e8f5e9;
  color: #66ca1a;
}

.status-delivered {
  background: #e8f5e9;
  color: #4caf50;
}

.status-cancelled {
  background: #ffebee;
  color: #f44336;
}

.order-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.order-section h3 {
  font-size: 18px;
  font-weight: 600;
  color: #252525;
  margin: 0 0 16px 0;
}

.order-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f8f8f8;
  border-radius: 8px;
}

.item-image {
  width: 80px;
  height: 80px;
  object-fit: contain;
  border-radius: 8px;
  /* background: white; */
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.item-name {
  font-weight: 500;
  color: #252525;
  margin-bottom: 8px;
}

.item-details {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.item-price {
  color: #666;
  font-size: 14px;
}

.item-subtotal {
  font-weight: 600;
  color: #252525;
}

.delivery-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.delivery-method {
  font-weight: 500;
  color: #252525;
}

.delivery-address {
  color: #666;
}

.delivery-cost {
  color: #666;
  font-size: 14px;
}

.order-total {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.total-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  color: #666;
}

.total-row.final {
  border-top: 1px solid #eee;
  margin-top: 8px;
  padding-top: 16px;
  color: #252525;
  font-weight: 600;
  font-size: 18px;
}

.order-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.cancel-button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: #ffebee;
  color: #f44336;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cancel-button:hover {
  background: #ffcdd2;
}

.error-state {
  text-align: center;
  padding: 40px 20px;
}

.error-state p {
  color: #f44336;
  margin-bottom: 20px;
}

.back-button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: #333;
  color: white;
  font-weight: 500;
  cursor: pointer;
}

@media (max-width: 480px) {
  .order-details {
    padding: 16px;
  }

  .order-header h2 {
    font-size: 20px;
  }

  .order-section {
    padding: 16px;
  }

  .order-item {
    padding: 12px;
  }

  .item-image {
    width: 60px;
    height: 60px;
  }

  .total-row.final {
    font-size: 16px;
  }
}
</style>
