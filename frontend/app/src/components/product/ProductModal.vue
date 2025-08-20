<script setup lang="ts">
/**
 * Компонент модального окна для отображения информации о товаре.
 */
import CloseButton from "@/components/icons/CloseButton.vue";
import { logger } from "@/utils/logger";
import { onMounted, onUnmounted } from "vue";

const props = defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
}>();

const lockScroll = () => {
  try {
    document.body.style.overflow = "hidden";
    document.body.style.paddingRight = `${window.innerWidth - document.documentElement.clientWidth}px`;
  } catch (err) {
    logger.error("Failed to lock scroll", { error: err });
  }
};

const unlockScroll = () => {
  try {
    document.body.style.overflow = "";
    document.body.style.paddingRight = "";
  } catch (err) {
    logger.error("Failed to unlock scroll", { error: err });
  }
};

const handleEscape = (e: KeyboardEvent) => {
  if (e.key === "Escape" && props.modelValue) {
    logger.debug("Modal closed by Escape key");
    emit("update:modelValue", false);
  }
};

onMounted(() => {
  document.addEventListener("keydown", handleEscape);
  if (props.modelValue) {
    lockScroll();
  }
  logger.debug("ProductModal mounted");
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleEscape);
  unlockScroll();
  logger.debug("ProductModal unmounted");
});
</script>

<template>
  <Transition name="modal-fade">
    <div
      v-if="modelValue"
      class="product-modal-overlay"
    >
      <!-- Кнопка закрытия вне wrapper -->
      <button
        class="product-modal-close"
        @click="$emit('update:modelValue', false)"
        aria-label="Закрыть"
      >
        <CloseButton />
      </button>

      <div class="product-modal-wrapper">
        <!-- Основной контейнер со скроллом -->
        <div class="modal-container">
          <div class="modal-scroll-container">
            <slot></slot>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style>
@import "@/assets/styles/product.css";
</style>
