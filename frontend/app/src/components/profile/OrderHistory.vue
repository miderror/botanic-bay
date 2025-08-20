<script setup lang="ts">
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import EmptyStateIcon from "@/components/icons/EmptyStateIcon.vue";
import OrderCard from "@/components/orders/OrderCard.vue";
import { useNotification } from "@/composables/useNotification";
import { orderService } from "@/services/orderService";
import type { IOrder } from "@/types/order";
import { logger } from "@/utils/logger";
import { computed, onMounted, ref } from "vue";

const orders = ref<IOrder[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);
const { showNotification } = useNotification();

// Вычисляемые свойства для группировки заказов по всем возможным статусам
const hasOrders = computed(() => orders.value.length > 0);

// Заказы со статусом "Ожидает оплаты"
const pendingOrders = computed(() => orders.value.filter((order) => order.status === "pending"));

// Заказы со статусом "Оплачен"
const paidOrders = computed(() => orders.value.filter((order) => order.status === "paid"));

// Заказы со статусом "В обработке"
const processingOrders = computed(() => orders.value.filter((order) => order.status === "processing"));

// Заказы со статусом "Отправлен"
const shippedOrders = computed(() => orders.value.filter((order) => order.status === "shipped"));

// Заказы со статусом "Доставлен"
const deliveredOrders = computed(() => orders.value.filter((order) => order.status === "delivered"));

// Заказы со статусом "Отменен"
const cancelledOrders = computed(() => orders.value.filter((order) => order.status === "cancelled"));

// Загрузка заказов
const loadOrders = async () => {
  try {
    isLoading.value = true;
    const response = await orderService.getMyOrders();
    // Сортируем заказы по дате создания (новые вверху)
    orders.value = response.items.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
    logger.info("Orders loaded successfully", {
      count: orders.value.length,
      pending: pendingOrders.value.length,
      paid: paidOrders.value.length,
      processing: processingOrders.value.length,
      shipped: shippedOrders.value.length,
      delivered: deliveredOrders.value.length,
      cancelled: cancelledOrders.value.length,
    });
  } catch (err) {
    error.value = "Не удалось загрузить заказы";
    logger.error("Failed to load orders", { error: err });
  } finally {
    isLoading.value = false;
  }
};

// Отмена заказа
const handleCancelOrder = async (orderId: string) => {
  try {
    await orderService.cancelOrder(orderId);
    await loadOrders(); // Перезагружаем список
    showNotification("Заказ отменен", "success");
    logger.info("Order cancelled successfully", { orderId });
  } catch (err) {
    showNotification("Не удалось отменить заказ", "error");
    logger.error("Failed to cancel order", { orderId, error: err });
  }
};

onMounted(() => {
  loadOrders();
});
</script>

<template>
  <div class="bb-order-history">
    <div class="bb-order-history__content">
      <!-- Загрузка -->
      <template v-if="isLoading">
        <LoadingSpinner />
      </template>

      <!-- Ошибка -->
      <template v-else-if="error">
        <div class="bb-order-history__error">{{ error }}</div>
      </template>

      <!-- Заказы -->
      <template v-else-if="hasOrders">
        <!-- Оплаченные (paid) -->
        <template v-if="paidOrders.length">
          <div class="bb-order-history__section">
            <div class="bb-order-history__section-title">Оплаченные</div>
            <OrderCard
              v-for="order in paidOrders"
              :key="order.id"
              :order="order"
              @cancel="handleCancelOrder"
            />
          </div>
        </template>

        <!-- В обработке (processing) -->
        <template v-if="processingOrders.length">
          <div class="bb-order-history__section">
            <div class="bb-order-history__section-title">В обработке</div>
            <OrderCard
              v-for="order in processingOrders"
              :key="order.id"
              :order="order"
              @cancel="handleCancelOrder"
            />
          </div>
        </template>

        <!-- Отправленные (shipped) -->
        <template v-if="shippedOrders.length">
          <div class="bb-order-history__section">
            <div class="bb-order-history__section-title">Отправленные</div>
            <OrderCard
              v-for="order in shippedOrders"
              :key="order.id"
              :order="order"
              @cancel="handleCancelOrder"
            />
          </div>
        </template>

        <!-- Доставленные (delivered) -->
        <template v-if="deliveredOrders.length">
          <div class="bb-order-history__section">
            <div class="bb-order-history__section-title">Доставленные</div>
            <OrderCard
              v-for="order in deliveredOrders"
              :key="order.id"
              :order="order"
              @cancel="handleCancelOrder"
            />
          </div>
        </template>
      </template>

      <!-- Нет заказов -->
      <template v-else>
        <div class="bb-order-history__empty">
          <EmptyStateIcon />
          <div class="bb-order-history__empty-text">У вас пока нет заказов</div>
          <router-link
            to="/catalog"
            class="bb-order-history__empty-action"
          >
            Перейти в каталог
          </router-link>
        </div>
      </template>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/order.css";
</style>
