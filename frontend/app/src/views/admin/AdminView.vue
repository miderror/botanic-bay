<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

// Состояние для отслеживания скролла
const isScrolled = ref(false);

// Обработчик скролла
const handleScroll = () => {
  isScrolled.value = window.scrollY > 100;
};

// Добавляем и удаляем слушатель скролла
onMounted(() => {
  window.addEventListener("scroll", handleScroll);
});

onUnmounted(() => {
  window.removeEventListener("scroll", handleScroll);
});
</script>

<template>
  <div class="admin-layout">
    <!-- Основной контейнер -->
    <div class="admin-container">
      <!-- Навигационное меню -->
      <nav
        class="admin-nav"
        :class="{ 'nav-scrolled': isScrolled }"
      >
        <div class="nav-content">
          <router-link
            to="/admin/products"
            class="nav-button"
            :class="{ active: $route.name === 'admin-products' }"
          >
            Товары
          </router-link>
          <router-link
            to="/admin/users"
            class="nav-button"
            :class="{ active: $route.name === 'admin-users' }"
          >
            Пользователи
          </router-link>
          <router-link
            to="/admin/orders"
            class="nav-button"
            :class="{ active: $route.name === 'admin-orders' }"
          >
            Заказы
          </router-link>
          <router-link
            to="/admin/payout-requests"
            class="nav-button"
            :class="{ active: $route.name === 'admin-payout-requests' }"
          >
            Заявки на вывод
          </router-link>
        </div>
      </nav>

      <!-- Контент страницы -->
      <main class="admin-content">
        <router-view v-slot="{ Component }">
          <transition
            name="fade"
            mode="out-in"
          >
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/admin.css";
</style>
