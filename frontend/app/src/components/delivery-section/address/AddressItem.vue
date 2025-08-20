<script setup lang="ts">
/**
 * Компонент для отображения элемента адреса с возможностью выбора, редактирования и удаления.
 * Позволяет пользователю выбрать адрес, открыть меню действий (редактировать, скопировать, удалить)
 * и отображает модальное окно для редактирования адреса.
 */
import UserAddressModal from "@/components/delivery-section/address/modal/UserAddressModal.vue";
import type { IUserAddress, IUserDeliveryPoint } from "@/types/order.ts";
import { onMounted, onUnmounted, ref } from "vue";

const props = defineProps<{
  address: IUserDeliveryPoint | IUserAddress;
  isFirst: boolean;
  isLast: boolean;
  isActive: boolean;
  selectAddress: (address: IUserDeliveryPoint | IUserAddress) => void;
  deleteAddress: (address: IUserDeliveryPoint | IUserAddress) => Promise<void>;
}>();

const isDropdownVisible = ref(false);
const isEditModalOpen = ref(false);
const dropdownRef = ref<HTMLElement | null>(null);

// Переключатель видимости
const toggleDropdown = () => {
  isDropdownVisible.value = !isDropdownVisible.value;
};

// Закрытие меню при клике вне его
const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isDropdownVisible.value = false;
  }
};

// Добавляем и удаляем обработчик события
onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside);
});

// Функция копирования адреса в буфер обмена
const copyAddress = async (event: MouseEvent) => {
  event.stopPropagation(); // предотвращаем срабатывание родительских обработчиков
  try {
    await navigator.clipboard.writeText(props.address.address);
    // Можно добавить уведомление о копировании
    console.log("Адрес скопирован");
  } catch (err) {
    console.error("Ошибка копирования адреса", err);
  }
  // Закрываем меню после действия
  isDropdownVisible.value = false;
};

// Функция для удаления адреса
const handleDeleteAddress = async (event: MouseEvent) => {
  event.stopPropagation();
  await props.deleteAddress(props.address);
  console.log("Удаление адреса", props.address);
  // Закрываем меню после действия
  isDropdownVisible.value = false;
};
</script>

<template>
  <div
    class="address-item"
    :class="{
      'first-item': isFirst,
      'last-item': isLast,
      active: isActive,
      'has-dropdown': isDropdownVisible,
    }"
    @click="selectAddress(address)"
  >
    <div class="radio">
      <div class="radio-inner"></div>
    </div>
    <div class="address-info">
      <div
        class="name"
        v-if="'name' in address && address.name"
      >
        {{ address.name }}
      </div>
      <div class="address">{{ address?.address }}</div>
    </div>
    <div
      class="action-dots"
      ref="dropdownRef"
      @click.stop="toggleDropdown"
    >
      <span></span>
      <span></span>
      <span></span>
      <!-- Выпадающее меню -->
      <div
        v-if="isDropdownVisible"
        class="dropdown-menu"
      >
        <button
          @click="() => (isEditModalOpen = true)"
          v-if="'apartment' in address && address?.apartment"
        >
          Редактировать
        </button>
        <button @click="copyAddress">Скопировать адрес</button>
        <button @click="handleDeleteAddress">Удалить</button>
      </div>
    </div>
  </div>

  <UserAddressModal
    v-if="'apartment' in address && address?.apartment"
    :is-open="isEditModalOpen"
    :address="address"
    @close="isEditModalOpen = false"
    @closeParentModal="isDropdownVisible = false"
  />
</template>

<style scoped>
.address-item {
  position: relative;
}

.address-item.active {
  z-index: 1;
}

.address-item.has-dropdown {
  z-index: 100;
}

.action-dots {
  cursor: pointer;
  position: relative;
  top: 0;
  right: 0;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: #fff;
  border: 1px solid #ddd;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 101;
  padding: 8px;
  display: flex;
  flex-direction: column;
}

.dropdown-menu button {
  background: none;
  border: none;
  padding: 6px 12px;
  text-align: left;
  cursor: pointer;
}

.dropdown-menu button:hover {
  background-color: #f0f0f0;
}
</style>
