<script setup lang="ts">
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import MultiImageUpload from "@/components/common/MultiImageUpload.vue";
import NotificationToast from "@/components/common/NotificationToast.vue";
import type { IAdminProduct } from "@/types/admin";
import { logger } from "@/utils/logger";
import { onMounted, onUnmounted, ref, watch } from "vue";

const props = defineProps<{
  product: IAdminProduct | null;
  categories: string[];
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "save", product: IAdminProduct): void;
}>();

// Состояние
const isLoading = ref(false);
const error = ref("");
const hasUnsavedChanges = ref(false);

// Уведомления
const showNotification = ref(false);
const notificationMessage = ref("");
const notificationType = ref<"success" | "error" | "info">("info");

// Локальное состояние формы
const form = ref({
  name: "",
  description: "",
  additional_description: "",
  price: 0,
  stock: 0,
  category: "",
  is_active: true,
  image_url: null as string | null,
  background_image_url: null as string | null,
  additional_images_urls: [] as string[],
});

// Функция для показа уведомлений
const showToast = (message: string, type: "success" | "error" | "info" = "info") => {
  notificationMessage.value = message;
  notificationType.value = type;
  showNotification.value = true;

  // Скрываем через 3 секунды
  setTimeout(() => {
    showNotification.value = false;
  }, 3000);
};

// Обработчик ошибок загрузки
const handleUploadError = (message: string) => {
  showToast(message, "error");
};

// Обработчик отправки формы
const handleSubmit = async () => {
  try {
    if (!form.value.name || form.value.price <= 0) {
      throw new Error("Заполните обязательные поля");
    }

    logger.debug("Submit form data:", {
      all: form.value,
      background: form.value.background_image_url,
      main: form.value.image_url,
      additional: form.value.additional_images_urls,
    });

    isLoading.value = true;

    const productData = {
      ...form.value,
      isActive: form.value.is_active,
      // Если это новый товар, добавляем недостающие поля
      id: props.product?.id ?? "", // Для нового товара будет пустая строка
      createdAt: props.product?.createdAt ?? new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      sku: props.product?.sku ?? null,
      // Добавляем поля изображений из формы
      image_url: form.value.image_url,
      background_image_url: form.value.background_image_url,
      additional_images_urls: form.value.additional_images_urls,
      total_orders: props.product?.total_orders ?? 0,
      last_ordered_at: props.product?.last_ordered_at ?? null,
    };

    // Добавляем подробный лог перед отправкой на сервер
    logger.debug("Submitting product data:", {
      formData: form.value,
      productData: productData,
      additionalImages: productData.additional_images_urls,
    });

    emit("save", productData);
    hasUnsavedChanges.value = false;
  } catch (err) {
    logger.error("Form validation failed", { error: err });
    error.value = err instanceof Error ? err.message : "Ошибка валидации формы";
  } finally {
    isLoading.value = false;
  }
};

// Отслеживаем изменения формы
watch(
  form,
  () => {
    hasUnsavedChanges.value = true;
  },
  { deep: true },
);

// При монтировании компонента инициализируем форму
onMounted(() => {
  logger.info("Initializing product form", {
    product: props.product,
    categories: props.categories,
  });

  // Блокируем прокрутку body
  document.body.style.overflow = "hidden";
  // Добавляем отступ равный ширине скроллбара, чтобы избежать скачка контента
  document.body.style.paddingRight = `${window.innerWidth - document.documentElement.clientWidth}px`;

  // Если редактируем существующий товар
  if (props.product) {
    form.value = {
      name: props.product.name,
      description: props.product.description,
      additional_description: props.product.additional_description || "",
      price: props.product.price,
      stock: props.product.stock,
      category: props.product.category || "",
      is_active: props.product.isActive,
      image_url: props.product.image_url,
      background_image_url: props.product.background_image_url,
      // Явно преобразуем в массив, если undefined
      additional_images_urls: Array.isArray(props.product.additional_images_urls)
        ? [...props.product.additional_images_urls]
        : [],
    };

    logger.debug("Form initialized with data:", {
      product: props.product,
      additional_description: props.product.additional_description,
      additional_images_urls: props.product.additional_images_urls,
    });
  } else {
    // Если создаем новый - устанавливаем значения по умолчанию
    form.value = {
      name: "",
      description: "",
      additional_description: "",
      price: 0,
      stock: 0,
      category: "",
      is_active: true,
      image_url: null,
      background_image_url: null,
      additional_images_urls: [],
    };
  }
});

// Возвращаем прокрутку при закрытии
onUnmounted(() => {
  document.body.style.overflow = "";
  document.body.style.paddingRight = "";
});
</script>

<template>
  <div class="admin-modal-overlay">
    <div class="admin-modal-content">
      <div class="admin-modal-header">
        <h2 class="admin-modal-title">{{ product ? "Редактирование товара" : "Новый товар" }}</h2>
        <button
          class="admin-modal-close-btn"
          @click="$emit('close')"
        >
          ✕
        </button>
      </div>

      <div class="admin-modal-body">
        <form
          @submit.prevent="handleSubmit"
          class="admin-product-form"
        >
          <div class="admin-form-group">
            <label class="admin-form-label">Название</label>
            <input
              v-model="form.name"
              type="text"
              required
              class="admin-form-input"
            />
          </div>

          <div class="admin-form-group">
            <label class="admin-form-label">Описание</label>
            <textarea
              v-model="form.description"
              class="admin-form-textarea"
              rows="5"
            ></textarea>
          </div>

          <div class="admin-form-group">
            <label class="admin-form-label">Дополнительное описание</label>
            <textarea
              v-model="form.additional_description"
              class="admin-form-textarea"
              rows="5"
            ></textarea>
          </div>

          <div class="admin-form-group">
            <label class="admin-form-label">Изображения товара</label>
            <MultiImageUpload
              v-model:mainImage="form.image_url"
              v-model:backgroundImage="form.background_image_url"
              v-model:additionalImages="form.additional_images_urls"
              @error="handleUploadError"
            />
          </div>

          <div class="admin-form-row">
            <div class="admin-form-group">
              <label class="admin-form-label">Цена</label>
              <input
                v-model.number="form.price"
                type="number"
                step="0.01"
                required
                class="admin-form-input"
              />
            </div>

            <div class="admin-form-group">
              <label class="admin-form-label">Количество</label>
              <input
                v-model.number="form.stock"
                type="number"
                required
                class="admin-form-input"
              />
            </div>
          </div>

          <div class="admin-form-group">
            <label class="admin-form-label">Категория</label>
            <select
              v-model="form.category"
              class="admin-form-select"
              required
            >
              <option value="">Выберите категорию</option>
              <option
                v-for="category in categories"
                :key="category"
                :value="category"
              >
                {{ category }}
              </option>
            </select>
          </div>

          <div class="admin-form-group">
            <label class="admin-checkbox-label">
              <input
                type="checkbox"
                v-model="form.is_active"
                class="admin-checkbox"
              />
              <span>Товар активен</span>
            </label>
          </div>

          <div
            v-if="error"
            class="admin-error-message"
          >
            {{ error }}
          </div>

          <div class="admin-form-actions">
            <button
              type="button"
              class="admin-btn admin-btn-cancel"
              :disabled="isLoading"
              @click="$emit('close')"
            >
              Отмена
            </button>
            <button
              type="submit"
              class="admin-btn admin-btn-primary"
              :disabled="isLoading"
            >
              <LoadingSpinner
                v-if="isLoading"
                small
              />
              <span v-else>Сохранить</span>
            </button>
          </div>
        </form>
      </div>
    </div>
    <NotificationToast
      :show="showNotification"
      :message="notificationMessage"
      :type="notificationType"
    />
  </div>
</template>

<style>
@import "@/assets/styles/admin.css";

/* Дополнительные стили для ProductEditModal */
.admin-product-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.admin-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.admin-checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-family: var(--admin-font-body);
  font-size: 12px;
  color: var(--admin-primary);
}

.admin-checkbox {
  width: 16px;
  height: 16px;
  accent-color: var(--admin-primary);
}

.admin-error-message {
  color: var(--admin-error);
  font-family: var(--admin-font-body);
  font-size: 12px;
  padding: 8px;
  background-color: rgba(255, 91, 91, 0.1);
  border-radius: 8px;
  margin-bottom: 16px;
}

/* Адаптивность для мобильных устройств */
@media (max-width: 480px) {
  .admin-form-row {
    grid-template-columns: 1fr;
  }

  .admin-modal-content {
    max-height: 85vh;
  }

  .admin-modal-body {
    padding: 12px;
  }
}
</style>
