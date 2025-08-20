<script setup lang="ts">
import UserRolesModal from "@/components/admin/UserRolesModal.vue";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import NotificationToast from "@/components/common/NotificationToast.vue";
import { useNotification } from "@/composables/useNotification";
import { ADMIN_USERS_PER_PAGE } from "@/config/pagination";
import { adminService } from "@/services/adminService";
import type { IAdminUser, IAdminUserFilter } from "@/types/admin";
import { logger } from "@/utils/logger";
import { onMounted, ref, watch } from "vue";

// Константы
const userRoles = ["user", "admin", "manager", "support"];

// Состояние
const users = ref<IAdminUser[]>([]);
const currentPage = ref(1);
const totalPages = ref(1);
const filters = ref<IAdminUserFilter>({
  username: "",
  telegram_id: undefined,
  role: "",
  is_active: undefined,
});

const isLoading = ref(false);
const showRolesModal = ref(false);
const selectedUser = ref<IAdminUser | null>(null);

// Уведомления
const { message, type, show, showNotification } = useNotification();

// Загрузка данных
const loadUsers = async () => {
  try {
    isLoading.value = true;
    const response = await adminService.getUsers(currentPage.value, ADMIN_USERS_PER_PAGE, filters.value);

    users.value = response.items;
    totalPages.value = response.pages;
  } catch (error) {
    logger.error("Failed to load users", { error });
    showNotification("Не удалось загрузить список пользователей", "error");
  } finally {
    isLoading.value = false;
  }
};

// Методы
const openRolesModal = (user: IAdminUser) => {
  selectedUser.value = user;
  showRolesModal.value = true;
};

const closeRolesModal = () => {
  selectedUser.value = null;
  showRolesModal.value = false;
};

const saveUserRoles = async (userId: string, roles: string[]) => {
  try {
    await adminService.updateUserRoles(userId, roles);
    showNotification("Роли пользователя обновлены", "success");
    await loadUsers();
    closeRolesModal();
  } catch (error) {
    logger.error("Failed to update user roles", { error });
    showNotification("Не удалось обновить роли пользователя", "error");
  }
};

const toggleUserBlock = async (user: IAdminUser) => {
  const action = user.is_active ? "заблокировать" : "разблокировать";
  if (!confirm(`Вы действительно хотите ${action} пользователя ${user.username}?`)) {
    return;
  }

  try {
    await adminService.toggleUserBlock(user.id);
    showNotification(`Пользователь успешно ${user.is_active ? "заблокирован" : "разблокирован"}`, "success");
    await loadUsers();
  } catch (error) {
    logger.error("Failed to toggle user block status", { error });
    showNotification("Не удалось изменить статус пользователя", "error");
  }
};

// Функция changePage
const changePage = async (newPage: number) => {
  try {
    if (newPage < 1 || newPage > totalPages.value) return;

    currentPage.value = newPage;
    // loadUsers будет вызван автоматически через watch
  } catch (error) {
    logger.error("Failed to change page", { error, newPage });
    showNotification("Не удалось загрузить страницу", "error");
  }
};

// Наблюдатели
watch(
  [currentPage, () => ({ ...filters.value })],
  async () => {
    try {
      await loadUsers();
    } catch (error) {
      logger.error("Failed to load users after filters/page change", { error });
    }
  },
  { deep: true },
);

// Инициализация
onMounted(() => {
  loadUsers();
});
</script>

<template>
  <div class="admin-users">
    <div class="admin-header">
      <h1>Управление пользователями</h1>
    </div>

    <!-- Фильтры -->
    <div class="admin-filters">
      <div class="admin-filter-group">
        <input
          v-model="filters.username"
          type="text"
          placeholder="Поиск по имени пользователя"
          class="admin-filter-input"
        />
        <input
          v-model="filters.telegram_id"
          type="number"
          placeholder="Telegram ID"
          class="admin-filter-input"
        />
      </div>

      <div class="admin-filter-group">
        <select
          v-model="filters.role"
          class="admin-filter-select"
        >
          <option value="">Все роли</option>
          <option
            v-for="role in userRoles"
            :key="role"
            :value="role"
          >
            {{ role }}
          </option>
        </select>
      </div>
    </div>

    <!-- Таблица пользователей -->
    <div class="admin-table-container">
      <template v-if="isLoading">
        <LoadingSpinner />
      </template>

      <template v-else-if="users.length === 0">
        <div class="admin-empty-state">
          <p>Пользователи не найдены</p>
        </div>
      </template>

      <template v-else>
        <table class="admin-table">
          <thead>
            <tr>
              <th>Telegram ID</th>
              <th>Имя пользователя</th>
              <th>Полное имя</th>
              <th>Роли</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="user in users"
              :key="user.id"
            >
              <td>{{ user.telegram_id }}</td>
              <td>{{ user.username }}</td>
              <td>{{ user.full_name }}</td>
              <td>
                <div class="admin-role-badges">
                  <span
                    v-for="role in user.roles"
                    :key="role"
                    class="admin-role-badge"
                  >
                    {{ role }}
                  </span>
                </div>
              </td>
              <td>
                <span
                  class="admin-status-badge"
                  :class="{
                    'admin-status-active': user.is_active,
                    'admin-status-inactive': !user.is_active,
                  }"
                >
                  {{ user.is_active ? "Активен" : "Заблокирован" }}
                </span>
              </td>
              <td class="admin-actions">
                <button
                  class="admin-action-btn edit"
                  @click="openRolesModal(user)"
                >
                  Роли
                </button>
                <button
                  class="admin-action-btn"
                  :class="user.is_active ? 'block' : 'unblock'"
                  @click="toggleUserBlock(user)"
                >
                  {{ user.is_active ? "Блокировать" : "Разблокировать" }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </template>
    </div>

    <!-- Пагинация -->
    <div class="admin-pagination">
      <button
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
        class="admin-page-btn"
      >
        ←
      </button>
      <span class="admin-page-info"> Страница {{ currentPage }} из {{ totalPages }} </span>
      <button
        :disabled="currentPage === totalPages"
        @click="changePage(currentPage + 1)"
        class="admin-page-btn"
      >
        →
      </button>
    </div>

    <!-- Модальное окно управления ролями -->
    <UserRolesModal
      v-if="showRolesModal"
      :user="selectedUser"
      @close="closeRolesModal"
      @save="saveUserRoles"
    />

    <!-- Уведомления -->
    <NotificationToast
      :show="show"
      :message="message"
      :type="type"
    />
  </div>
</template>

<style>
@import "@/assets/styles/admin.css";
</style>
