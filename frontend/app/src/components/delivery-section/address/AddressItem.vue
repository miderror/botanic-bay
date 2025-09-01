<script setup lang="ts">
/**
 * Компонент для отображения элемента адреса с возможностью выбора, редактирования и удаления.
 * Видимость выпадающего меню управляется родительским компонентом.
 */
import UserAddressModal from "@/components/delivery-section/address/modal/UserAddressModal.vue";
import type { IUserAddress, IUserDeliveryPoint } from "@/types/order.ts";
import { ref } from "vue";

const props = defineProps<{
  address: IUserDeliveryPoint | IUserAddress;
  isFirst: boolean;
  isLast: boolean;
  isActive: boolean;
  isDropdownOpen: boolean;
  selectAddress: (address: IUserDeliveryPoint | IUserAddress) => void;
  deleteAddress: (address: IUserDeliveryPoint | IUserAddress) => Promise<void>;
}>();

const emit = defineEmits<{
  (e: "toggle-dropdown"): void;
}>();

const isEditModalOpen = ref(false);

const copyAddress = async (event: MouseEvent) => {
  event.stopPropagation();
  try {
    await navigator.clipboard.writeText(props.address.address);
    console.log("Адрес скопирован");
  } catch (err) {
    console.error("Ошибка копирования адреса", err);
  }
  emit("toggle-dropdown");
};

const handleDeleteAddress = async (event: MouseEvent) => {
  event.stopPropagation();
  await props.deleteAddress(props.address);
  console.log("Удаление адреса", props.address);
  emit("toggle-dropdown");
};

const openEditModal = (event: MouseEvent) => {
  event.stopPropagation();
  isEditModalOpen.value = true;
};
</script>

<template>
  <div
    class="address-item"
    :class="{
      'first-item': isFirst,
      'last-item': isLast,
      active: isActive,
      'has-dropdown': isDropdownOpen,
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
      @click.stop="$emit('toggle-dropdown')"
    >
      <span></span>
      <span></span>
      <span></span>
      <transition name="fade-dropdown">
        <div
          v-if="isDropdownOpen"
          class="dropdown-menu"
        >
          <button
            @click="openEditModal"
            v-if="'apartment' in address && address?.apartment"
          >
            Редактировать
          </button>
          <button @click="copyAddress">Скопировать адрес</button>
          <button @click="handleDeleteAddress">Удалить</button>
        </div>
      </transition>
    </div>
  </div>

  <UserAddressModal
    v-if="'apartment' in address && address?.apartment"
    :is-open="isEditModalOpen"
    :address="address"
    @close="isEditModalOpen = false"
    @closeParentModal="$emit('toggle-dropdown')"
  />
</template>

<style scoped>
.address-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 1;
}

.address-info {
  flex-grow: 1;
}

.address-item.active {
  z-index: 2;
}

.address-item.has-dropdown {
  z-index: 3;
}

.action-dots {
  cursor: pointer;
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
  padding: 4px;
  display: flex;
  flex-direction: column;
  width: max-content;
}

.dropdown-menu button {
  background: none;
  border: none;
  padding: 8px 12px;
  text-align: left;
  cursor: pointer;
  border-radius: 6px;
  font-size: 14px;
  transition: background-color 0.2s;
}

.dropdown-menu button:hover {
  background-color: #f5f5f5;
}

.fade-dropdown-enter-active,
.fade-dropdown-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.fade-dropdown-enter-from,
.fade-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>