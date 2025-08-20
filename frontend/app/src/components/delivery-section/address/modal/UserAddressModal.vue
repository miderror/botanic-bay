<script setup lang="ts">
/**
 * Компонент модального окна для редактирования дополнительных полей адреса пользователя.
 * Позволяет пользователю ввести дополнительные данные адреса, такие как
 * квартира, подъезд, этаж и код домофона. Все поля обязательны для заполнения.
 * Создаётся новый адрес, если ID отсутствует, или обновляет существующий адрес.
 */
import BaseModal from "@/components/common/BaseModal.vue";
import { useNotification } from "@/composables/useNotification.ts";
import { useDeliveryPreferences } from "@/stores/deliveryPreferences.ts";
import type { IUserAddress } from "@/types/order.ts";
import { computed, ref, watch } from "vue";

const props = defineProps<{
  isOpen: boolean;
  address: IUserAddress;
}>();

const emit = defineEmits(["close", "closeParentModal"]);

const { showNotification } = useNotification();
const { saveAddress, updateAddress } = useDeliveryPreferences();

const apartment = ref<number | null>(null);
const entrance = ref<number | null>(null);
const floor = ref<number | null>(null);
const intercomCode = ref<number | null>(null);

// Инициализация полей формы значениями из адреса
const initializeFields = () => {
  apartment.value = props.address.apartment || null;
  entrance.value = props.address.entrance || null;
  floor.value = props.address.floor || null;
  intercomCode.value = props.address.intercom_code || null;
};

// Следим за изменениями адреса и обновляем поля
watch(() => props.address, initializeFields, { immediate: true });

const apartmentError = ref(false);
const entranceError = ref(false);
const floorError = ref(false);
const intercomCodeError = ref(false);

const validateApartment = () => {
  const value = String(apartment.value || "").trim();
  apartmentError.value = !apartment.value || value === "" || !/^\d+$/.test(value);
};

const validateEntrance = () => {
  const value = String(entrance.value || "").trim();
  entranceError.value = !entrance.value || value === "" || !/^\d+$/.test(value);
};

const validateFloor = () => {
  const value = String(floor.value || "").trim();
  floorError.value = !floor.value || value === "" || !/^\d+$/.test(value);
};

const validateIntercomCode = () => {
  const value = String(intercomCode.value || "").trim();
  intercomCodeError.value = !intercomCode.value || value === "" || !/^\d+$/.test(value);
};

// Функция для фильтрации ввода только цифр
const onlyNumbers = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const value = input.value.replace(/\D/g, ""); // Удаляем все не-цифры
  input.value = value;

  // Обновляем соответствующее reactive значение
  const inputElement = event.target as HTMLInputElement;
  if (inputElement.placeholder.includes("Квартира")) {
    apartment.value = value ? Number(value) : null;
  } else if (inputElement.placeholder.includes("Подъезд")) {
    entrance.value = value ? Number(value) : null;
  } else if (inputElement.placeholder.includes("Этаж")) {
    floor.value = value ? Number(value) : null;
  } else if (inputElement.placeholder.includes("Код домофона")) {
    intercomCode.value = value ? Number(value) : null;
  }
};

// Общая функция для проверки всех полей
const validateAllFields = () => {
  validateApartment();
  validateEntrance();
  validateFloor();
  validateIntercomCode();
};

// Проверка валидности всех полей
const isAllFieldsValid = () => {
  return (
    apartment.value &&
    entrance.value &&
    floor.value &&
    intercomCode.value &&
    !apartmentError.value &&
    !entranceError.value &&
    !floorError.value &&
    !intercomCodeError.value
  );
};

const isLoading = ref(false);
const isButtonDisabled = computed(() => {
  return !isAllFieldsValid();
});

const onSaveButtonClick = async () => {
  // Валидация всех полей
  validateAllFields();

  if (!isAllFieldsValid()) {
    return;
  }

  if (!props.address) return;

  isLoading.value = true;
  try {
    const addressData = {
      ...props.address,
      apartment: apartment.value!,
      entrance: entrance.value!,
      floor: floor.value!,
      intercom_code: intercomCode.value!,
    };

    // Если у адреса есть ID, обновляем, иначе создаем новый
    if (props.address.id) {
      await updateAddress(props.address.id, addressData);
    } else {
      await saveAddress(addressData);
    }

    emit("close");
    emit("closeParentModal");
  } catch (e) {
    console.error("❌ Ошибка при сохранении адреса:", e);
    showNotification("Произошла ошибка при сохранении адреса", "error");
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <BaseModal
    :modelValue="isOpen"
    @update:modelValue="$emit('close')"
    minimized
    :overlayBg="false"
    :closeButton="true"
    :closeOnOverlayClick="true"
  >
    <div class="modal-location-content">
      <h2 class="modal-location-name">
        {{ address.address.split(", ").slice(0, 2).join(", ") }}
      </h2>

      <div class="modal-location-info-container">
        <div class="modal-location-input-grid">
          <input
            v-model="apartment"
            :class="['modal-input', { 'error-border': apartmentError }]"
            placeholder="Квартира*"
            @input="onlyNumbers"
            @blur="validateApartment"
          />
          <input
            v-model="entrance"
            :class="['modal-input', { 'error-border': entranceError }]"
            placeholder="Подъезд*"
            @input="onlyNumbers"
            @blur="validateEntrance"
          />
          <input
            v-model="floor"
            :class="['modal-input', { 'error-border': floorError }]"
            placeholder="Этаж*"
            @input="onlyNumbers"
            @blur="validateFloor"
          />
          <input
            v-model="intercomCode"
            :class="['modal-input', { 'error-border': intercomCodeError }]"
            placeholder="Код домофона*"
            @input="onlyNumbers"
            @blur="validateIntercomCode"
          />
        </div>
      </div>

      <div class="modal-location-button-container">
        <button
          class="modal-button"
          :disabled="isButtonDisabled || isLoading"
          @click="onSaveButtonClick"
        >
          {{ isLoading ? "СОХРАНЕНИЕ..." : props.address.id ? "ОБНОВИТЬ АДРЕС" : "СОХРАНИТЬ АДРЕС" }}
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
@import "@/assets/styles/modal.css";
@import "@/assets/styles/location-modal.css";

.modal-input.error-border::placeholder {
  color: var(--modal-input-error);
}
</style>
