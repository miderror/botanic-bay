<script setup lang="ts">
/**
 * Компонент для отображения подробной информации о товаре в модальном окне.
 */
import CartQuantityControl from "@/components/cart/CartQuantityControl.vue";
import NotificationToast from "@/components/common/NotificationToast.vue";
import ProductModal from "@/components/product/ProductModal.vue";
import { useCart } from "@/composables/useCart";
import { useImageUrl } from "@/composables/useImageUrl";
import { useNotification } from "@/composables/useNotification";
import { useProductPolling } from "@/composables/useProductPolling";
import type { IProduct } from "@/types/product";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import DOMPurify from "dompurify";
import { marked } from "marked";
import { computed, onMounted, ref, watch } from "vue";

const props = defineProps<{
  product: IProduct | null;
  isOpen: boolean;
}>();
defineEmits<{
  (e: "update:isOpen", value: boolean): void;
}>();

const modalContent = ref<HTMLElement | null>(null);
const isLoading = ref(false);
const isDescriptionExpanded = ref(false);

const { getImageUrl, handleImageError } = useImageUrl();
const { availableQuantity } = useProductPolling(props.product?.id || "");
const { cart, addToCart } = useCart();
const { showNotification, show, message, type } = useNotification();

marked.setOptions({
  gfm: true,
  breaks: true,
});

const headerBackgroundStyle = computed(() => {
    const url = getImageUrl(props.product?.background_image_url || null);
    if (url.includes('placeholder.jpg')) {
        return { backgroundColor: "var(--product-header-bg)" };
    }
    return {
        backgroundImage: `url(${url})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
    };
});

const headerImageUrl = computed(() => getImageUrl(props.product?.header_image_url || null));
const hasHeaderImage = computed(() => !!props.product?.header_image_url);
const mainImageUrl = computed(() => getImageUrl(props.product?.image_url || null));
const sanitizedDescription = computed(() => {
  if (!props.product?.description) return "";
  const htmlContent = marked(props.product.description);
  return DOMPurify.sanitize(htmlContent as string);
});
const sanitizedAdditionalDescription = computed(() => {
  if (!props.product?.additional_description) return "";
  const htmlContent = marked(props.product.additional_description);
  const centeredContent = `<div align="center">${htmlContent}</div>`;
  return DOMPurify.sanitize(centeredContent, { ADD_TAGS: ["div"], ADD_ATTR: ["align"] });
});
const isInCart = computed(() => cart.value?.items.some((item) => item.product_id === props.product?.id));

const toggleDescriptionExpanded = () => {
  isDescriptionExpanded.value = !isDescriptionExpanded.value;
};

const handleAddToCart = async () => {
  if (!props.product || isLoading.value) return;
  try {
    isLoading.value = true;
    await addToCart(props.product.id, 1);
    showNotification("Товар добавлен в корзину", "success");
  } catch (err) {
    logger.error("Failed to add product to cart from modal", { productId: props.product.id, error: err });
  } finally {
    isLoading.value = false;
  }
};


onMounted(() => {
  if (modalContent.value) modalContent.value.scrollTop = 0;
});
watch(() => props.product?.id, () => {
  isDescriptionExpanded.value = false;
});
</script>

<template>
    <ProductModal :modelValue="isOpen" @update:modelValue="$emit('update:isOpen', $event)">
        <div v-if="product" class="product-modal-content" ref="modalContent">
            <div class="product-header">
                <div class="header-background" :style="headerBackgroundStyle">
                    <div class="decorative-overlay"></div>
                </div>
            </div>
            <div v-if="hasHeaderImage" class="product-header-image-container">
                <img :src="headerImageUrl" :alt="product.name" class="header-image" @error="handleImageError" />
            </div>
            <div class="product-content-wrapper">
                <div class="product-main-info">
                    <div class="product-image-container">
                        <img :src="mainImageUrl" :alt="product.name" class="product-main-image" @error="handleImageError" />
                    </div>
                    <div class="product-info">
                        <h1 class="product-title">{{ product.name }}</h1>
                        <div class="product-description" v-html="sanitizedDescription"></div>
                    </div>
                </div>
                <div class="product-additional-info" v-if="product.additional_description">
                    <div class="additional-description markdown-content" :class="{ 'description-collapsed': !isDescriptionExpanded }" v-html="sanitizedAdditionalDescription" @click="toggleDescriptionExpanded"></div>
                    <div v-if="!isDescriptionExpanded" class="description-expand-hint" @click="toggleDescriptionExpanded">
                        Нажмите для показа полного описания
                    </div>
                </div>
                <div class="product-purchase">
                    <div class="modal-product-price">{{ formatPrice(product.price) }}</div>
                    <div class="modal-product-stock">В наличии {{ availableQuantity }} шт.</div>
                    <CartQuantityControl v-if="isInCart" :product-id="product.id" :max-quantity="product.stock" :disabled="isLoading" />
                    <button v-else class="modal-buy-button" :disabled="isLoading || availableQuantity === 0" @click="handleAddToCart">
                        {{ isLoading ? "ДОБАВЛЕНИЕ ..." : "КУПИТЬ" }}
                    </button>
                </div>
            </div>
        </div>
    </ProductModal>
    <NotificationToast :show="show" :message="message" :type="type" />
</template>

<style>
@import "@/assets/styles/product.css";
.modal-buy-button:disabled {
  background-color: var(--catalog-button-disabled);
  cursor: not-allowed;
}
</style>