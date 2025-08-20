<script setup lang="ts">
import BaseModal from "@/components/common/BaseModal.vue";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import AddressList from "@/components/delivery-section/address/AddressList.vue";
import LocationSelector from "@/components/delivery-section/address/LocationSelector.vue";
import DeliveryToggle from "@/components/delivery-section/DeliveryToggle.vue";
import { useCheckoutStore } from "@/stores/checkout.ts";
import { useDeliveryPreferences } from "@/stores/deliveryPreferences.ts";
import type { IUserAddress, IUserDeliveryPoint } from "@/types/order.ts";
import { DeliveryMethod } from "@/types/order.ts";
import { logger } from "@/utils/logger.ts";
import { storeToRefs } from "pinia";
import { computed, onMounted, ref, watch } from "vue";

defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

// Store
const checkoutStore = useCheckoutStore();
const {
  deliveryMethod: currentMethod,
  selectedPickupPoint,
  selectedUserAddress,
} = storeToRefs(checkoutStore);

const deliveryPreferences = useDeliveryPreferences();
const { addresses, deliveryPoints } = storeToRefs(deliveryPreferences);

// Состояние
const isLoading = ref(false);
const isLocationSelectorShown = ref(false);

// Вычисляемые свойства
const isAddressSelected = computed(() => {
  return currentMethod.value === DeliveryMethod.PICKUP
    ? !!selectedPickupPoint.value
    : !!selectedUserAddress.value;
});

const handleLocationSelectorModalClose = () => {
  isLocationSelectorShown.value = false;
  logger.debug("Address modal closed");
};

const selectAddress = (address: IUserDeliveryPoint | IUserAddress) => {
  if (currentMethod.value === DeliveryMethod.PICKUP) {
    checkoutStore.setPickupPoint(address as IUserDeliveryPoint);
    logger.debug("Pickup point selected", { pointId: address.id });
  } else {
    checkoutStore.setUserAddress(address as IUserAddress);
    logger.debug("User address selected", { addressId: address.id });
  }
};

const deleteAddress = async (address: IUserDeliveryPoint | IUserAddress) => {
  if (currentMethod.value === DeliveryMethod.PICKUP) {
    await deliveryPreferences.deleteDeliveryPoint(address as IUserDeliveryPoint);
    logger.debug("Pickup point deleted", { pointId: address.id });
  } else {
    await deliveryPreferences.deleteAddress(address as IUserAddress);
    logger.debug("User address selected", { addressId: address.id });
  }
};

const handleSave = () => {
  logger.debug("Save button clicked", {
    selectedAddress:
      currentMethod.value === DeliveryMethod.PICKUP ? selectedPickupPoint.value : selectedUserAddress.value,
  });
  // Явно сохраняем выбранный адрес в localStorage через store
  if (currentMethod.value === DeliveryMethod.PICKUP && selectedPickupPoint.value) {
    checkoutStore.setPickupPoint(selectedPickupPoint.value);
  } else if (currentMethod.value === DeliveryMethod.COURIER && selectedUserAddress.value) {
    checkoutStore.setUserAddress(selectedUserAddress.value);
  }
  emit("close");
};

const handleAddPickupPoint = () => {
  isLocationSelectorShown.value = true;
  logger.info("Add pickup point button clicked");
};

const handleAddUserAddress = () => {
  logger.info("Add address button clicked");
  isLocationSelectorShown.value = true;
};

const loadAddresses = async () => {
  try {
    isLoading.value = true;
    await Promise.all([deliveryPreferences.fetchAddresses(), deliveryPreferences.fetchDeliveryPoints()]);
  } catch (error) {
    logger.error("Failed to load addresses", { error });
  } finally {
    isLoading.value = false;
  }
};

watch(isLocationSelectorShown, () => {
  if (!isLocationSelectorShown.value) {
    window.Telegram?.WebApp?.enableVerticalSwipes();
  }
});

onMounted(() => {
  loadAddresses();
});
</script>

<template>
  <BaseModal
    :modelValue="isOpen"
    @update:modelValue="$emit('close')"
    title="Адрес доставки"
    fullscreen
  >
    <div class="address-modal-content">
      <!-- Переключатель способа доставки -->
      <DeliveryToggle />

      <LocationSelector
        :isOpen="isLocationSelectorShown"
        :currentMethod="currentMethod"
        @close="handleLocationSelectorModalClose"
      />

      <div v-if="!isLocationSelectorShown">
        <!-- Список адресов с загрузкой -->
        <LoadingSpinner v-if="isLoading" />

        <div v-else>
          <AddressList
            v-if="currentMethod === DeliveryMethod.PICKUP"
            :addresses="deliveryPoints"
            :selectedAddress="selectedPickupPoint"
            :selectAddress="selectAddress"
            :handleAddAddress="handleAddPickupPoint"
            :deleteAddress="deleteAddress"
            buttonLabel="ДОБАВИТЬ ПУНКТ ВЫДАЧИ +"
          />

          <AddressList
            v-else
            :addresses="addresses"
            :selectedAddress="selectedUserAddress"
            :selectAddress="selectAddress"
            :handleAddAddress="handleAddUserAddress"
            :deleteAddress="deleteAddress"
            buttonLabel="ДОБАВИТЬ АДРЕС +"
          />
        </div>
      </div>

      <!-- Контейнер для кнопки сохранения -->
      <div class="save-button-container">
        <button
          class="save-button"
          :disabled="!isAddressSelected"
          @click="handleSave"
        >
          СОХРАНИТЬ
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style>
@import "@/assets/styles/modal.css";
@import "@/assets/styles/address-modal.css";
</style>
