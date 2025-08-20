<script setup lang="ts">
defineProps<{
  message?: string;
}>();
</script>

<template>
  <div class="loading-spinner">
    <div class="spinner"></div>
    <div
      v-if="message"
      class="message"
    >
      {{ message }}
    </div>
  </div>
</template>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.message {
  margin-top: 10px;
  color: #666;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
