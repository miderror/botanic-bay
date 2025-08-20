<script setup lang="ts">
/**
 * Компонент для навигации по профилю пользователя
 * Содержит ссылки на различные разделы профиля
 */
const tabs = [
  { name: "orders", route: "profile-orders", title: "ЗАКАЗЫ" },
  { name: "business", route: "profile-business", title: "БИЗНЕС" },
  { name: "account", route: "profile-account", title: "ДАННЫЕ АККАУНТА" },
];
</script>

<template>
  <nav class="bb-profile-nav">
    <router-link
      v-for="tab in tabs"
      :key="tab.name"
      :to="{ name: tab.route }"
      class="bb-profile-nav__btn"
      :class="{ active: $route.name === tab.route }"
    >
      {{ tab.title }}
    </router-link>
  </nav>
</template>
