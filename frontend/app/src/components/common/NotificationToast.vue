<script setup lang="ts">
defineProps<{
  show: boolean;
  message: string;
  type: "success" | "error" | "info";
}>();
</script>

<template>
  <Transition name="toast">
    <div
      v-if="show"
      class="toast"
      :class="type"
    >
      {{ message }}
    </div>
  </Transition>
</template>

<style scoped>
.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  z-index: 1000;
}

.success {
  background-color: #66ca1a;
}

.error {
  background-color: #f44336;
}

.info {
  background-color: #2196f3;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-30px);
}
</style>
