<script setup lang="ts">
/**
 * Компонент выбора способа доставки
 * Отображает список доступных методов доставки и выбранный адрес
 * Позволяет пользователю выбрать метод и добавить/изменить адрес доставки
 */
import DeliveryToggle from "@/components/delivery-section/DeliveryToggle.vue";
import AddressModal from "@/components/delivery-section/address/modal/AddressModal.vue";
import LocationIcon from "@/components/icons/LocationIcon.vue";
import { useCheckout } from "@/composables/useCheckout.ts";
import { DeliveryMethod } from "@/types/order.ts";
import { logger } from "@/utils/logger.ts";
import { computed, ref } from "vue";

withDefaults(
  defineProps<{
    type?: "delivery-method" | "saved-addresses";
  }>(),
  {
    type: "delivery-method",
  },
);

const { currentDeliveryMethod, selectedPickupPoint, selectedUserAddress } = useCheckout();

const showAddressModal = ref(false);

/**
 * Отображаемый адрес доставки в зависимости от выбранного метода
 */
const displayAddress = computed(() => {
  if (currentDeliveryMethod.value === DeliveryMethod.PICKUP) {
    const point = selectedPickupPoint.value;
    return point ? `${point.name}\n${point.address}` : "Укажите адрес доставки";
  }
  const address = selectedUserAddress.value;
  return address ? address.address : "Укажите адрес доставки";
});

/**
 * Флаг наличия выбранного адреса
 */
const hasAddress = computed(() => {
  return currentDeliveryMethod.value === DeliveryMethod.PICKUP
    ? !!selectedPickupPoint.value
    : !!selectedUserAddress.value;
});

const deliveryInfo = computed(() => {
  return currentDeliveryMethod.value === DeliveryMethod.PICKUP
    ? "Доставка в пункт выдачи, бесплатно"
    : "Доставка осуществляется курьером";
});

/**
 * Обработчик закрытия модального окна выбора адреса
 */
const handleAddressModalClose = () => {
  showAddressModal.value = false;
  logger.debug("Address modal closed");
};

/**
 * Обработчик нажатия на кнопку добавления/изменения адреса
 */
const handleAddressAction = () => {
  showAddressModal.value = true;
  logger.debug("Address modal opened");
};
</script>

<template>
  <section class="w-full">
    <h2
      class="section-title"
      style="margin-top: 0px !important"
    >
      {{ type == "delivery-method" ? "Способ доставки" : "Адреса" }}
    </h2>
    <div class="delivery-section">
      <!-- 1. Сначала кнопки выбора метода -->
      <DeliveryToggle />

      <!-- 2. Затем блок с адресом -->
      <div class="address-block">
        <LocationIcon class="location-icon" />
        <div class="address-text">
          {{ displayAddress }}
        </div>
      </div>

      <!-- 3. И наконец кнопка действия -->
      <div class="address-action">
        <button
          class="action-button"
          :class="{ disabled: !currentDeliveryMethod }"
          @click="handleAddressAction"
          :disabled="!currentDeliveryMethod"
        >
          <span class="action-button-text">
            {{ hasAddress ? "ИЗМЕНИТЬ АДРЕС" : "ДОБАВИТЬ АДРЕС +" }}
          </span>
        </button>
      </div>
    </div>

    <div
      class="delivery-info"
      v-if="type == 'delivery-method'"
    >
      {{ deliveryInfo }}
    </div>
  </section>

  <!-- Модальное окно выбора адреса -->
  <AddressModal
    v-if="showAddressModal"
    :isOpen="showAddressModal"
    @close="handleAddressModalClose"
  />
</template>

<style>
@import "@/assets/styles/delivery-section.css";
</style>
