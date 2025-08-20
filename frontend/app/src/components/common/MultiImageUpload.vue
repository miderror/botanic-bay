<script setup lang="ts">
import config from "@/config";
import { logger } from "@/utils/logger";
import type { PropType } from "vue";
import { computed, ref, watch } from "vue";
import ImageUpload from "./ImageUpload.vue";

const props = defineProps({
  mainImage: {
    type: String as PropType<string | null>,
    default: null,
  },
  backgroundImage: {
    type: String as PropType<string | null>,
    default: null,
  },
  additionalImages: {
    type: Array as PropType<string[]>,
    default: () => [], // Возвращаем пустой массив по умолчанию
    required: false,
  },
});

const emit = defineEmits<{
  (e: "update:mainImage", value: string): void;
  (e: "update:backgroundImage", value: string): void;
  (e: "update:additionalImages", value: string[]): void;
  (e: "error", message: string): void;
}>();

// Состояние для drag&drop
const isDragging = ref(false);

// Вычисляем, можно ли добавить ещё изображения
const canAddMore = computed(() => {
  return props.additionalImages.length < config.maxAdditionalProductImages;
});

// Обработка загрузки основного изображения
const handleMainImageUpload = (imageUrl: string) => {
  logger.info("Main product image uploaded", { imageUrl });
  emit("update:mainImage", imageUrl);
};

// Добавляем обработчик загрузки фонового изображения
const handleBackgroundImageUpload = (imageUrl: string) => {
  logger.info("Background product image uploaded", { imageUrl });
  emit("update:backgroundImage", imageUrl);
};

// Обработка загрузки дополнительного изображения
const handleAdditionalImageUpload = (imageUrl: string) => {
  if (!canAddMore.value) {
    emit("error", `Превышен лимит дополнительных изображений (${config.maxAdditionalProductImages})`);
    return;
  }

  logger.info("Additional product image uploaded", {
    imageUrl,
    currentCount: props.additionalImages.length,
  });

  const newImages = [...props.additionalImages, imageUrl];
  emit("update:additionalImages", newImages);
};

// Удаление дополнительного изображения
const removeAdditionalImage = (index: number) => {
  logger.info("Removing additional image", { index });
  const newImages = [...props.additionalImages];
  newImages.splice(index, 1);
  emit("update:additionalImages", newImages);
};

// Drag & Drop функционал
const handleDragStart = (e: DragEvent, index: number) => {
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", index.toString());
    isDragging.value = true;
  }
};

const handleDragOver = (e: DragEvent) => {
  e.dataTransfer!.dropEffect = "move";
};

const handleDrop = (e: DragEvent, newIndex: number) => {
  isDragging.value = false;
  e.stopPropagation();

  const oldIndex = parseInt(e.dataTransfer!.getData("text/plain"));
  if (oldIndex === newIndex) return;

  const newImages = [...props.additionalImages];
  const [movedItem] = newImages.splice(oldIndex, 1);
  newImages.splice(newIndex, 0, movedItem);

  logger.info("Reordered additional images", { oldIndex, newIndex });
  emit("update:additionalImages", newImages);
};

// Добавим watch для отладки
watch(
  () => props.additionalImages,
  (newVal) => {
    logger.debug("Additional images updated:", {
      images: newVal,
    });
  },
  { deep: true },
);
</script>

<template>
  <div class="multi-image-upload">
    <!-- Основное изображение - отдельная секция -->
    <div class="main-image-section">
      <h4>Основное изображение товара</h4>
      <div class="main-image-container">
        <ImageUpload
          :model-value="mainImage"
          @update:model-value="handleMainImageUpload"
          @error="$emit('error', $event)"
        />
      </div>
    </div>

    <!-- Добавляем секцию фонового изображения -->
    <div class="background-image-section">
      <h4>Фоновое изображение товара</h4>
      <div class="background-image-container">
        <ImageUpload
          :model-value="backgroundImage"
          @update:model-value="handleBackgroundImageUpload"
          @error="$emit('error', $event)"
        />
      </div>
    </div>

    <!-- Разделитель -->
    <div class="divider">
      <span>Дополнительные фотографии товара</span>
    </div>

    <!-- Дополнительные изображения -->
    <div class="additional-images-section">
      <!-- Список загруженных изображений -->
      <div
        class="images-grid"
        :class="{ 'is-dragging': isDragging }"
      >
        <!-- Существующие дополнительные изображения -->
        <div
          v-for="(image, index) in additionalImages"
          :key="index"
          class="image-item"
          draggable="true"
          @dragstart="handleDragStart($event, index)"
          @dragover.prevent="handleDragOver"
          @drop="handleDrop($event, index)"
        >
          <img
            :src="image"
            :alt="`Additional image ${index + 1}`"
          />
          <button
            class="remove-btn"
            @click="removeAdditionalImage(index)"
            title="Удалить изображение"
          >
            ×
          </button>
          <div class="image-number">{{ index + 1 }}</div>
        </div>

        <!-- Кнопка добавления нового изображения -->
        <div
          class="add-image"
          v-if="canAddMore"
        >
          <ImageUpload
            :model-value="null"
            @update:model-value="handleAdditionalImageUpload"
            @error="$emit('error', $event)"
          >
            <template #placeholder>
              <div class="add-placeholder">
                <span>+</span>
                <small>Добавить фото</small>
              </div>
            </template>
          </ImageUpload>
        </div>
      </div>

      <!-- Подсказка с ограничением -->
      <div class="hint">
        <small>Можно добавить до {{ config.maxAdditionalProductImages }} дополнительных фотографий</small>
        <small
          v-if="!canAddMore"
          class="warning"
        >
          Достигнут лимит дополнительных фотографий
        </small>
      </div>
    </div>
  </div>
</template>

<style scoped>
.multi-image-upload {
  display: flex;
  flex-direction: column;
  gap: 20px;
  font-family: "Inter", sans-serif;
}

.main-image-section,
.background-image-section {
  border-radius: 20px;
  padding: 16px;
  background: rgba(240.12, 240.12, 240.12, 0.4);
  backdrop-filter: blur(4px);
}

.main-image-section h4,
.background-image-section h4 {
  margin-bottom: 12px;
  color: #252525;
  font-size: 12px;
  font-family: "Open Sans Hebrew", sans-serif;
  font-weight: 700;
  line-height: 12px;
  text-align: center;
}

.divider {
  text-align: center;
  position: relative;
  margin: 16px 0;
}

.divider::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  height: 1px;
  background: rgba(120, 120, 120, 0.2);
  z-index: 0;
}

.divider span {
  position: relative;
  background: white;
  padding: 0 10px;
  color: #787878;
  font-size: 12px;
  font-family: "Open Sans Hebrew", sans-serif;
  font-weight: 700;
  line-height: 12px;
  z-index: 1;
}

.additional-images-section {
  border-radius: 20px;
  padding: 16px;
  background: rgba(240.12, 240.12, 240.12, 0.4);
  backdrop-filter: blur(4px);
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
  padding: 8px;
  min-height: 100px;
}

.images-grid.is-dragging {
  background: rgba(120, 120, 120, 0.1);
  border-radius: 12px;
}

.image-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  cursor: move;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-number {
  position: absolute;
  bottom: 4px;
  left: 4px;
  background: rgba(36, 36, 36, 0.7);
  color: white;
  padding: 2px 6px;
  border-radius: 100px;
  font-size: 10px;
  font-family: "Inter", sans-serif;
  font-weight: 700;
}

.remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(36, 36, 36, 0.7);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: rgba(255, 91, 91, 0.8);
}

.add-image {
  aspect-ratio: 1;
  border-radius: 12px;
  transition: all 0.2s;
  background: white;
  border: 1px dashed #787878;
  overflow: hidden;
}

.add-image :deep(.upload-area) {
  border: none !important;
  height: 100%;
}

.add-image :deep(.upload-area:hover) {
  background: rgba(120, 120, 120, 0.05);
}

.add-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #787878;
}

.add-placeholder span {
  font-size: 24px;
  margin-bottom: 4px;
}

.add-placeholder small {
  font-size: 10px;
  font-family: "Inter", sans-serif;
  font-weight: 500;
}

.hint {
  margin-top: 12px;
  text-align: center;
  color: #787878;
  font-size: 10px;
  font-family: "Pontano Sans", sans-serif;
  font-weight: 400;
  line-height: 10px;
}

.warning {
  color: #ff5b5b;
  display: block;
  margin-top: 4px;
  font-weight: 700;
}
</style>
