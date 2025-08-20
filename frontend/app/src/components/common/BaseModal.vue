<script setup lang="ts">
import CloseButton from "@/components/icons/CloseButton.vue";
import { logger } from "@/utils/logger";
import { onMounted, onUnmounted } from "vue";

// Пропсы
const props = withDefaults(
  defineProps<{
    modelValue: boolean;
    title?: string;
    contentClass?: string;
    fullscreen?: boolean;
    minimized?: boolean;
    overlayBg?: boolean;
    closeOnOverlayClick?: boolean;
    closeButton?: boolean;
  }>(),
  {
    overlayBg: true,
    closeOnOverlayClick: true,
    closeButton: true,
  },
);

// События
const emit = defineEmits<{
  (e: "update:modelValue", value: boolean): void;
}>();

const onOverlayClick = () => {
  if (!props.closeOnOverlayClick) return;
  emit("update:modelValue", false);
};

// Блокировка скролла при открытии модального окна
const lockScroll = () => {
  try {
    document.body.style.overflow = "hidden";
    document.body.style.paddingRight = `${window.innerWidth - document.documentElement.clientWidth}px`;
  } catch (err) {
    logger.error("Failed to lock scroll", { error: err });
  }
};

// Разблокировка скролла при закрытии
const unlockScroll = () => {
  try {
    document.body.style.overflow = "";
    document.body.style.paddingRight = "";
  } catch (err) {
    logger.error("Failed to unlock scroll", { error: err });
  }
};

// Обработка клавиши Escape
const handleEscape = (e: KeyboardEvent) => {
  if (e.key === "Escape" && props.modelValue) {
    emit("update:modelValue", false);
  }
};

// Монтирование компонента
onMounted(() => {
  document.addEventListener("keydown", handleEscape);
  if (props.modelValue) {
    lockScroll();
  }
});

// Размонтирование компонента
onUnmounted(() => {
  document.removeEventListener("keydown", handleEscape);
  unlockScroll();
});
</script>

<template>
  <Transition name="modal-fade">
    <div
      v-if="modelValue"
      :class="['modal-overlay', { 'modal-overlay-bg': overlayBg, 'modal-overlay--minimized': minimized }]"
      @click.self="onOverlayClick"
    >
      <div
        class="modal-content"
        :class="[
          contentClass,
          {
            'modal-content--fullscreen': fullscreen,
            'modal-content--minimized': minimized,
          },
        ]"
      >
        <!-- Заголовок -->
        <div
          v-if="title"
          class="modal-header"
        >
          <h2 class="modal-title">{{ title }}</h2>
        </div>

        <!-- Кнопка закрытия -->
        <button
          v-if="closeButton"
          class="modal-close"
          @click="$emit('update:modelValue', false)"
          aria-label="Закрыть"
        >
          <CloseButton />
        </button>

        <!-- Контент -->
        <div
          class="modal-body"
          :class="{ 'has-title': title }"
        >
          <slot></slot>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style>
@import "@/assets/styles/modal.css";
</style>
