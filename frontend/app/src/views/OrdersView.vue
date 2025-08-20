<script setup lang="ts"></script>

<template>
  <div class="orders-view">
    <div class="orders-tabs">
      <router-link
        :to="{ name: 'orders-cart' }"
        custom
        v-slot="{ isActive, navigate }"
      >
        <button
          class="tab-button"
          :class="{ active: isActive }"
          @click="navigate"
        >
          Корзина
        </button>
      </router-link>

      <router-link
        :to="{ name: 'orders-list' }"
        custom
        v-slot="{ isActive, navigate }"
      >
        <button
          class="tab-button"
          :class="{ active: isActive }"
          @click="navigate"
        >
          История заказов
        </button>
      </router-link>
    </div>

    <router-view v-slot="{ Component }">
      <transition
        name="fade"
        mode="out-in"
      >
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<style scoped>
.orders-view {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.orders-tabs {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.tab-button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  background: #f5f5f5;
  color: #666;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-button.active {
  background: #333;
  color: white;
}

.orders-content {
  min-height: 400px;
}

/* Mobile Responsive */
@media (max-width: 480px) {
  .orders-view {
    padding: 16px;
  }

  .orders-tabs {
    gap: 8px;
  }

  .tab-button {
    padding: 8px 16px;
    font-size: 14px;
  }
}
</style>
