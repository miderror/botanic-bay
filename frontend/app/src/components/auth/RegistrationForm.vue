<script setup lang="ts">
import { useTelegramWebApp } from "@/composables/useTelegramWebApp";
import { useAuthStore } from "@/stores/auth";
import { onMounted } from "vue";

const authStore = useAuthStore();
const { user } = useTelegramWebApp();

onMounted(async () => {
  if (user.value) {
    await authStore.register();
  }
});
</script>

<style scoped>
.registration-form {
  padding: 20px;
  max-width: 400px;
  margin: 0 auto;
}

.success {
  text-align: center;
  color: #2ecc71;
}

.error {
  color: #e74c3c;
  text-align: center;
  padding: 10px;
  border-radius: 4px;
  background-color: #fce4e4;
}
</style>
