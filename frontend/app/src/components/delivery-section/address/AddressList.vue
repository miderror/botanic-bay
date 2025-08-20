<script setup lang="ts">
/**
 * Компонент для отображения списка адресов пользователя или ПВЗ.
 */
import type { IUserAddress, IUserDeliveryPoint } from "@/types/order.ts";
import AddressItem from "./AddressItem.vue";

defineProps<{
  addresses: (IUserDeliveryPoint | IUserAddress)[];
  selectedAddress: IUserAddress | IUserDeliveryPoint | null;
  selectAddress: (address: IUserDeliveryPoint | IUserAddress) => void;
  deleteAddress: (address: IUserDeliveryPoint | IUserAddress) => Promise<void>;
  handleAddAddress: () => void;
  buttonLabel: string;
}>();
</script>

<template>
  <div class="addresses-list">
    <AddressItem
      v-for="(address, index) in addresses"
      :key="address.id"
      :address="address"
      :isFirst="index === 0"
      :isLast="index === addresses.length - 1"
      :isActive="selectedAddress?.id === address.id"
      :selectAddress="selectAddress"
      :deleteAddress="deleteAddress"
    />

    <button
      class="add-button"
      @click="handleAddAddress"
    >
      {{ buttonLabel }}
    </button>
  </div>
</template>
