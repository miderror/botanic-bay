<script setup lang="ts">
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";

defineProps<{
  visible: boolean;
  message: string;
}>();
</script>

<template>
  <Transition name="fade">
    <div
      v-if="visible"
      class="loading-overlay"
    >
      <div class="loading-overlay__content">
        <LoadingSpinner />
        <div class="loading-overlay__message">{{ message }}</div>
      </div>
    </div>
  </Transition>
</template>

<style>
.loading-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(36, 36, 36, 0.7);
  backdrop-filter: blur(2px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-overlay__content {
  padding: 20px;
  background: transparent;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.loading-overlay__message {
  color: white;
  font-size: 12px;
  font-family: "Inter", sans-serif;
  font-weight: 500;
  line-height: 12px;
  text-align: center;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
