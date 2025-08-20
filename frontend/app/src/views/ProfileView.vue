<script setup lang="ts">
/**
 * Компонент для отображения профиля пользователя
 * Содержит навигацию и динамическую загрузку компонентов профиля
 */
import ProfileNav from "@/components/profile/ProfileNav.vue";
</script>

<template>
  <!-- Обертка для фона на всю ширину -->
  <div class="profile-wrapper">
    <!-- Контейнер для контента фиксированной ширины -->
    <div class="profile">
      <ProfileNav />
      <router-view v-slot="{ Component }">
        <transition
          name="fade"
          mode="out-in"
        >
          <component :is="Component" />
        </transition>
      </router-view>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/profile.css";
</style>
