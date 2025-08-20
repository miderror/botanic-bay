<script setup lang="ts">
/**
 * Компонент для отображения подробной информации о товаре в модальном окне.
 * Позволяет пользователю просматривать изображения, описание и добавлять товар в корзину.
 */
import CartQuantityControl from "@/components/cart/CartQuantityControl.vue";
import NotificationToast from "@/components/common/NotificationToast.vue";
import ProductModal from "@/components/product/ProductModal.vue";
import { useCart } from "@/composables/useCart";
import { useNotification } from "@/composables/useNotification";
import { useProductPolling } from "@/composables/useProductPolling";
import type { IProduct } from "@/types/product";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import DOMPurify from "dompurify";
import { marked } from "marked";
import { computed, onMounted, ref, watch } from "vue";

// Пропсы компонента
const props = defineProps<{
  product: IProduct | null;
  isOpen: boolean;
}>();

// События компонента
defineEmits<{
  (e: "update:isOpen", value: boolean): void;
}>();

// Локальное состояние
const currentAdditionalImageIndex = ref(0);
const modalContent = ref<HTMLElement | null>(null);
const isLoading = ref(false);
const isDescriptionExpanded = ref(false);

// Подключаем необходимые composables
const { availableQuantity } = useProductPolling(props.product?.id || "");
const { cart, addToCart } = useCart();
const { showNotification, show, message, type } = useNotification();

// Настройка markdown парсера
marked.setOptions({
  gfm: true,
  breaks: true,
});

// Вычисляемые свойства
const headerBackgroundStyle = computed(() => {
  if (!props.product?.background_image_url) {
    return {
      backgroundColor: "var(--product-header-bg)",
    };
  }

  return {
    backgroundImage: `url(${props.product.background_image_url})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
    backgroundRepeat: "no-repeat",
  };
});

const additionalImages = computed(() => {
  if (!props.product?.additional_images_urls) return [];
  return props.product.additional_images_urls.filter(Boolean);
});

const hasAdditionalImages = computed(() => additionalImages.value.length > 0);
const hasMultipleAdditionalImages = computed(() => additionalImages.value.length > 1);
const currentAdditionalImage = computed(
  () => additionalImages.value[currentAdditionalImageIndex.value] || "",
);

const mainImageUrl = computed(() => {
  if (!props.product?.image_url) return "/images/placeholder.jpg";
  return props.product.image_url;
});

const sanitizedDescription = computed(() => {
  if (!props.product?.description) return "";
  const htmlContent = marked(props.product.description);
  return DOMPurify.sanitize(htmlContent as string);
});

const sanitizedAdditionalDescription = computed(() => {
  if (!props.product?.additional_description) return "";
  // Сначала преобразуем markdown в HTML
  const htmlContent = marked(props.product.additional_description);
  // Потом оборачиваем в центрирующий div
  const centeredContent = `<div align="center">${htmlContent}</div>`;
  return DOMPurify.sanitize(centeredContent, {
    ADD_TAGS: ["div"],
    ADD_ATTR: ["align"],
  });
});

const isInCart = computed(() => {
  return cart.value?.items.some((item) => item.product_id === props.product?.id);
});

// Методы компонента
const prevAdditionalImage = () => {
  if (currentAdditionalImageIndex.value > 0) {
    currentAdditionalImageIndex.value--;
  }
};

const nextAdditionalImage = () => {
  if (currentAdditionalImageIndex.value < additionalImages.value.length - 1) {
    currentAdditionalImageIndex.value++;
  }
};

const toggleDescriptionExpanded = () => {
  isDescriptionExpanded.value = !isDescriptionExpanded.value;
};

// Обработчик добавления в корзину
const handleAddToCart = async () => {
  if (!props.product || isLoading.value) return;

  try {
    isLoading.value = true;
    await addToCart(props.product.id, 1);
    showNotification("Товар добавлен в корзину", "success");

    logger.info("Product added to cart from modal", {
      productId: props.product.id,
      productName: props.product.name,
    });
  } catch (err) {
    logger.error("Failed to add product to cart from modal", {
      productId: props.product.id,
      error: err,
    });
  } finally {
    isLoading.value = false;
  }
};

const handleImageError = (e: Event) => {
  const img = e.target as HTMLImageElement;
  const originalSrc = img.src;

  if (!originalSrc.includes("placeholder.jpg")) {
    img.src = "/images/placeholder.jpg";
    logger.warn("Product image load failed, using placeholder", {
      originalSrc,
      productId: props.product?.id,
    });
  }
};

// Хуки жизненного цикла
onMounted(() => {
  if (modalContent.value) {
    modalContent.value.scrollTop = 0;
  }
});

// Сброс состояния описания при смене продукта
watch(
  () => props.product?.id,
  () => {
    isDescriptionExpanded.value = false;
  },
);
</script>

<template>
  <ProductModal
    :modelValue="isOpen"
    @update:modelValue="$emit('update:isOpen', $event)"
  >
    <div
      v-if="product"
      class="product-modal-content"
      ref="modalContent"
    >
      <!-- Шапка с фоновым изображением -->
      <div class="product-header">
        <div
          class="header-background"
          :style="headerBackgroundStyle"
        >
          <div class="decorative-overlay"></div>
        </div>
      </div>

      <!-- Карусель дополнительных изображений -->
      <div
        v-if="hasAdditionalImages"
        class="additional-images-carousel"
      >
        <button
          v-if="hasMultipleAdditionalImages"
          class="carousel-btn prev"
          @click="prevAdditionalImage"
          aria-label="Предыдущее изображение"
        >
          <span>&larr;</span>
        </button>

        <div class="carousel-container">
          <div class="carousel-image-wrapper">
            <img
              :src="currentAdditionalImage"
              :alt="product.name"
              class="carousel-image"
              @error="handleImageError"
            />
          </div>
        </div>

        <button
          v-if="hasMultipleAdditionalImages"
          class="carousel-btn next"
          @click="nextAdditionalImage"
          aria-label="Следующее изображение"
        >
          <span>&rarr;</span>
        </button>
      </div>

      <!-- Основная информация о товаре -->
      <div class="product-content-wrapper">
        <div class="product-main-info">
          <div class="product-image-container">
            <img
              :src="mainImageUrl"
              :alt="product.name"
              class="product-main-image"
              @error="handleImageError"
            />
          </div>

          <div class="product-info">
            <h1 class="product-title">{{ product.name }}</h1>
            <div
              class="product-description"
              v-html="sanitizedDescription"
            ></div>
          </div>
        </div>

        <!-- Дополнительное описание товара -->
        <div
          class="product-additional-info"
          v-if="product.additional_description"
        >
          <div
            class="additional-description markdown-content"
            :class="{ 'description-collapsed': !isDescriptionExpanded }"
            v-html="sanitizedAdditionalDescription"
            @click="toggleDescriptionExpanded"
          ></div>
          <div
            v-if="!isDescriptionExpanded"
            class="description-expand-hint"
            @click="toggleDescriptionExpanded"
          >
            Нажмите для показа полного описания
          </div>
        </div>

        <!-- Блок покупки с ценой и контролем количества -->
        <div class="product-purchase">
          <div class="modal-product-price">
            {{ formatPrice(product.price) }}
          </div>

          <div class="modal-product-stock">В наличии {{ availableQuantity }} шт.</div>

          <!-- Используем единый компонент контроля количества -->
          <CartQuantityControl
            v-if="isInCart"
            :product-id="product.id"
            :max-quantity="product.stock"
            :disabled="isLoading"
          />
          <button
            v-else
            class="modal-buy-button"
            :disabled="isLoading || availableQuantity === 0"
            @click="handleAddToCart"
          >
            {{ isLoading ? "ДОБАВЛЕНИЕ ..." : "КУПИТЬ" }}
          </button>
        </div>
      </div>
    </div>
  </ProductModal>

  <!-- Уведомление отображается сверху по центру страницы -->
  <NotificationToast
    :show="show"
    :message="message"
    :type="type"
  />
</template>

<style>
@import "@/assets/styles/product.css";

.modal-buy-button:disabled {
  background-color: var(--catalog-button-disabled);
  cursor: not-allowed;
}
</style>
