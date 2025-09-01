<script setup lang="ts">
/**
 * Компонент для отображения списка адресов пользователя или ПВЗ.
 * Управляет состоянием видимости выпадающих меню для дочерних элементов.
 */
import type { IUserAddress, IUserDeliveryPoint } from "@/types/order.ts";
import { onMounted, onUnmounted, ref } from "vue";
import AddressItem from "./AddressItem.vue";

defineProps<{
  addresses: (IUserDeliveryPoint | IUserAddress)[];
  selectedAddress: IUserAddress | IUserDeliveryPoint | null;
  selectAddress: (address: IUserDeliveryPoint | IUserAddress) => void;
  deleteAddress: (address: IUserDeliveryPoint | IUserAddress) => Promise<void>;
  handleAddAddress: () => void;
  buttonLabel: string;
}>();

const openDropdownId = ref<string | null>(null);
const listRef = ref<HTMLElement | null>(null);

const toggleDropdown = (addressId: string) => {
  if (openDropdownId.value === addressId) {
    openDropdownId.value = null;
  } else {
    openDropdownId.value = addressId;
  }
};

const handleClickOutside = (event: MouseEvent) => {
  if (listRef.value && !listRef.value.contains(event.target as Node)) {
    openDropdownId.value = null;
  }
};

onMounted(() => {
  document.addEventListener("click", handleClickOutside, true);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside, true);
});
</script>

<template>
  <div
    class="addresses-list"
    ref="listRef"
  >
    <AddressItem
      v-for="(address, index) in addresses"
      :key="address.id"
      :address="address"
      :isFirst="index === 0"
      :isLast="index === addresses.length - 1"
      :isActive="selectedAddress?.id === address.id"
      :is-dropdown-open="openDropdownId === address.id"
      :selectAddress="selectAddress"
      :deleteAddress="deleteAddress"
      @toggle-dropdown="toggleDropdown(address.id!)"
    />

    <button
      class="add-button"
      @click="handleAddAddress"
    >
      {{ buttonLabel }}
    </button>
  </div>
</template>