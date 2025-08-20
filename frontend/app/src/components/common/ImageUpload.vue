<script setup lang="ts">
import { adminService } from "@/services/adminService";
import { logger } from "@/utils/logger";
import { ref } from "vue";

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

const isLoading = ref(false);

const validateFile = (file: File): string | null => {
  if (!ALLOWED_TYPES.includes(file.type)) {
    return "Разрешены только изображения в форматах JPG, PNG и WEBP";
  }

  if (file.size > MAX_FILE_SIZE) {
    return "Размер файла не должен превышать 5MB";
  }

  return null;
};

defineProps<{
  modelValue: string | null; // Теперь всегда будет строка или null
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
  (e: "error", message: string): void;
  (e: "success", message: string): void;
}>();

const fileInput = ref<HTMLInputElement | null>(null);

const triggerFileInput = () => {
  fileInput.value?.click();
};

const handleFileSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files?.length) return;

  await uploadFile(input.files[0]);
};

const handleDrop = async (event: DragEvent) => {
  const file = event.dataTransfer?.files[0];
  if (!file) return;

  await uploadFile(file);
};

const uploadFile = async (file: File) => {
  try {
    // Валидируем файл
    const error = validateFile(file);
    if (error) {
      emit("error", error);
      return;
    }

    isLoading.value = true;

    // Используем adminService вместо прямого fetch
    const result = await adminService.uploadProductImage(file);

    emit("update:modelValue", result.image_url);
    emit("success", "Изображение успешно загружено");
  } catch (error) {
    logger.error("Failed to upload image", { error });
    emit("error", error instanceof Error ? error.message : "Не удалось загрузить изображение");
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="image-upload">
    <div
      class="upload-area"
      :class="{
        'has-image': modelValue,
        'is-loading': isLoading,
      }"
      @click="triggerFileInput"
      @dragover.prevent
      @drop.prevent="handleDrop"
    >
      <template v-if="isLoading">
        <div class="loading">Загрузка...</div>
      </template>
      <template v-else>
        <img
          v-if="modelValue"
          :src="modelValue"
          class="preview"
        />
        <div
          v-else
          class="placeholder"
        >
          <!-- <i class="upload-icon">📷</i> -->
          <span
            >Нажмите или перетащите изображение<br />
            <small>JPG, PNG или WEBP, до 5MB</small></span
          >
        </div>
      </template>
    </div>
    <input
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      class="hidden"
      @change="handleFileSelect"
    />
  </div>
</template>

<style scoped>
/* Добавим стили для состояния загрузки */
.is-loading {
  opacity: 0.7;
  pointer-events: none;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #666;
}

.image-upload {
  width: 100%;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: #666;
}

.upload-area.has-image {
  border-style: solid;
}

.preview {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
}

.placeholder {
  color: #666;
  font-size: 12px;
}

.upload-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.hidden {
  display: none;
}
</style>
