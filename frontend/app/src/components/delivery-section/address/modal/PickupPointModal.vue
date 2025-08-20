<script setup lang="ts">
import ClockIcon from "@/assets/images/clock.svg";
import BaseModal from "@/components/common/BaseModal.vue";
import { useNotification } from "@/composables/useNotification.ts";
import { useDeliveryPreferences } from "@/stores/deliveryPreferences.ts";
import type { IDeliveryPoint } from "@/types/cdek.ts";

const props = defineProps<{
  isOpen: boolean;
  point: IDeliveryPoint | null;
}>();

const emit = defineEmits(["close", "closeParentModal"]);

const OFFICE_TYPES = {
  POSTAMAT: "Постамат",
  PVZ: "Пункт выдачи",
  ALL: "Пункт выдачи",
};

const { showNotification } = useNotification();
const { saveDeliveryPoint } = useDeliveryPreferences();

const onAddButtonClick = async () => {
  if (!props.point) return;
  try {
    await saveDeliveryPoint(props.point);
    emit("close");
    emit("closeParentModal");
  } catch {
    showNotification("Произошла ошибка при добавлении данного ПВЗ", "error");
  }
};
</script>

<template>
  <BaseModal
    :modelValue="isOpen"
    @update:modelValue="$emit('close')"
    minimized
    :overlayBg="false"
  >
    <div class="modal-location-content">
      <h2 class="modal-location-name">{{ point?.type ? OFFICE_TYPES[point.type] : '' }}</h2>
      <div class="modal-location-info-container">
        <p class="modal-location-info">{{ point?.location.address }}</p>
        <p class="modal-location-info icon-container">
          <img :src="ClockIcon" />
          {{ point?.work_time }}
        </p>
      </div>

      <div class="modal-location-button-container">
        <button
          class="modal-button"
          @click="onAddButtonClick"
        >
          ДОБАВИТЬ ЭТОТ ПУНКТ
        </button>
      </div>
    </div>
  </BaseModal>
</template>

<style>
@import "@/assets/styles/modal.css";
@import "@/assets/styles/location-modal.css";
</style>
