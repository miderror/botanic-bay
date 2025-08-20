<script setup lang="ts">
import type { IAdminUser } from "@/types/admin";
import { logger } from "@/utils/logger";
import { computed, onMounted, ref } from "vue";

const props = defineProps<{
  user: IAdminUser;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", userId: string, roles: string[]): void;
}>();

// Роли с описаниями
const roleDescriptions: Record<string, string> = {
  user: "Обычный пользователь",
  admin: "Администратор",
  manager: "Менеджер магазина",
  support: "Служба поддержки",
};

// Список всех доступных ролей
const availableRoles = Object.keys(roleDescriptions);

// Reactive состояние выбранных ролей
const selectedRoles = ref<string[]>([]);

// Проверка наличия изменений
const hasChanges = computed(() => {
  // Сравниваем массивы с учетом порядка
  const originalRoles = props.user.roles.slice().sort();
  const currentRoles = selectedRoles.value.slice().sort();

  return JSON.stringify(originalRoles) !== JSON.stringify(currentRoles);
});

// Инициализация ролей при монтировании
onMounted(() => {
  // Гарантируем, что роль 'user' всегда присутствует
  selectedRoles.value = props.user.roles.includes("user") ? props.user.roles : ["user", ...props.user.roles];

  logger.debug("User roles initialized", {
    userId: props.user.id,
    initialRoles: selectedRoles.value,
  });
});

// Обработчик сохранения ролей
const handleSave = () => {
  try {
    // Логируем попытку обновления
    logger.info("Updating user roles", {
      userId: props.user.id,
      currentRoles: props.user.roles,
      newRoles: selectedRoles.value,
    });

    // Эмитим событие обновления с id пользователя и новыми ролями
    emit("save", props.user.id, selectedRoles.value);
  } catch (error) {
    // Логируем любые ошибки
    logger.error("Failed to update user roles", {
      userId: props.user.id,
      error,
    });
  }
};
</script>

<template>
  <div
    class="admin-modal-overlay"
    @click.self="$emit('close')"
  >
    <div class="admin-modal-content">
      <div class="admin-modal-header">
        <h2 class="admin-modal-title">Управление ролями</h2>
        <button
          class="admin-modal-close-btn"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div class="admin-modal-body">
        <p class="admin-user-info">{{ user.full_name }} (@{{ user.username || "без username" }})</p>

        <div class="admin-roles-list">
          <label
            v-for="role in availableRoles"
            :key="role"
            class="admin-role-checkbox"
          >
            <input
              type="checkbox"
              :value="role"
              v-model="selectedRoles"
              :disabled="role === 'user'"
              class="admin-checkbox"
            />
            {{ roleDescriptions[role] }}
          </label>
        </div>

        <div class="admin-form-actions">
          <button
            type="button"
            class="admin-btn admin-btn-cancel"
            @click="$emit('close')"
          >
            Отмена
          </button>
          <button
            type="button"
            class="admin-btn admin-btn-primary"
            @click="handleSave"
            :disabled="!hasChanges"
          >
            Сохранить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
@import "@/assets/styles/admin.css";

/* Дополнительные стили специфичные для этого компонента */
.admin-user-info {
  color: var(--admin-gray);
  margin-bottom: 16px;
  text-align: center;
  font-size: 12px;
  font-family: var(--admin-font-body);
  font-weight: 500;
}

.admin-roles-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.admin-role-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 12px;
  font-family: var(--admin-font-body);
  color: var(--admin-primary);
}

.admin-role-checkbox input[disabled] {
  cursor: not-allowed;
  opacity: 0.5;
}

.admin-checkbox {
  accent-color: var(--admin-primary);
  width: 16px;
  height: 16px;
}
</style>
