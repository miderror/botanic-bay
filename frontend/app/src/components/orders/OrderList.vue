<script setup lang="ts">
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import { useNotification } from "@/composables/useNotification";
import { orderService } from "@/services/orderService";
import type { IOrder } from "@/types/order";
import { logger } from "@/utils/logger";
import { onMounted, ref } from "vue";
import OrderCard from "./OrderCard.vue";

const orders = ref<IOrder[]>([]);
const isLoading = ref(true);
const error = ref<string | null>(null);
const { showNotification } = useNotification();

// Загрузка заказов
const loadOrders = async () => {
  try {
    isLoading.value = true;
    const response = await orderService.getMyOrders();
    orders.value = response.items;
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
  } catch (err) {
    showNotification("Не удалось отменить заказ", "error");
    logger.error("Failed to cancel order", {
      orderId,
      error: err,
    });
  }
};

onMounted(() => {
  loadOrders();
});
</script>

<template>
  <div class="orders-container">
    <!-- Tabs -->
    <nav class="profile-tabs">
      <router-link
        to="/profile/orders"
        class="tab-item"
        active-class="active"
      >
        ЗАКАЗЫ
      </router-link>
      <router-link
        to="/profile/business"
        class="tab-item"
      >
        БИЗНЕС
      </router-link>
      <router-link
        to="/profile/account"
        class="tab-item"
      >
        ДАННЫЕ АККАУНТА
      </router-link>
    </nav>

    <!-- Orders list -->
    <div class="orders-list">
      <template v-if="isLoading">
        <LoadingSpinner />
      </template>

      <template v-else-if="error">
        <div class="error-message">
          {{ error }}
        </div>
      </template>

      <template v-else-if="orders.length === 0">
        <div class="empty-state">
          <h3>У вас пока нет заказов</h3>
          <router-link
            to="/catalog"
            class="empty-action"
          >
            Перейти в каталог
          </router-link>
        </div>
      </template>

      <template v-else>
        <OrderCard
          v-for="order in orders"
          :key="order.id"
          :order="order"
          @cancel="handleCancelOrder"
        />
      </template>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/order.css";
</style>
