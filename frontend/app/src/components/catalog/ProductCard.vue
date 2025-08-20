<script setup lang="ts">
import CartQuantityControl from "@/components/cart/CartQuantityControl.vue";
import ProductView from "@/components/product/ProductView.vue";
import { useCart } from "@/composables/useCart";
import { useProductPolling } from "@/composables/useProductPolling";
import type { IProduct } from "@/types/product";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import { computed, ref, watch } from "vue";

// Props
const props = defineProps<{
  product: IProduct;
}>();

// Composables
const { cart, addToCart, removeFromCart, updateQuantity } = useCart();

// State
const availableQuantity = ref<number | null>(null);
const isModalOpen = ref(false);

try {
  const polling = useProductPolling(props.product.id);
  availableQuantity.value = polling.availableQuantity.value;

  watch(polling.availableQuantity, (newValue) => {
    availableQuantity.value = newValue;
  });
} catch (error) {
  logger.error("Error in ProductCard setup", { error });
}

// Computed
const displayQuantity = computed(() => {
  return availableQuantity.value ?? props.product.stock;
});

const isInCart = computed(() => {
  return cart.value?.items.some((item) => item.product_id === props.product.id);
});

const imageUrl = computed(() => {
  if (!props.product.image_url) {
    return "/images/placeholder.jpg";
  }

  if (props.product.image_url.startsWith("http") || props.product.image_url.startsWith("/media")) {
    return props.product.image_url;
  }

  const mediaUrl = `/media/products/${props.product.image_url}`;
  logger.debug("Using media URL:", { mediaUrl });

  return mediaUrl;
});

// Methods
const showProductDetails = () => {
  logger.debug("Product data before opening modal:", {
    id: props.product.id,
    name: props.product.name,
    background_image_url: props.product.background_image_url,
    image_url: props.product.image_url,
    allFields: Object.keys(props.product),
  });

  logger.info("Opening product details modal", {
    productId: props.product.id,
    productName: props.product.name,
  });
  isModalOpen.value = true;
};

const handleAddToCart = async () => {
  try {
    await addToCart(props.product.id, 1);
  } catch (err) {
    logger.error("Failed to add to cart", {
      productId: props.product.id,
      error: err,
    });
  }
};

const handleQuantityUpdate = async (productId: string, quantity: number) => {
  try {
    if (quantity === 0) {
      await removeFromCart(productId);
    } else {
      await updateQuantity(productId, quantity);
    }
  } catch (err) {
    logger.error("Failed to update quantity", {
      productId,
      quantity,
      error: err,
    });
  }
};

const handleImageError = (e: Event) => {
  const img = e.target as HTMLImageElement;
  const originalSrc = img.src;

  if (!originalSrc.includes("placeholder.jpg")) {
    img.src = "/images/placeholder.jpg";
    logger.warn("Product image load failed, using placeholder", {
      originalSrc,
      productId: props.product.id,
    });
  }
};
</script>

<template>
  <div class="product-card">
    <div
      class="product-image"
      @click="showProductDetails"
    >
      <img
        :src="imageUrl"
        :alt="product.name"
        @error="handleImageError"
      />
    </div>

    <div class="product-details">
      <div class="product-name">{{ product.name.toUpperCase() }}</div>
      <div class="product-price">{{ formatPrice(product.price) }}</div>
      <div class="product-stock">В наличии {{ displayQuantity }} шт.</div>
    </div>

    <div class="product-controls">
      <CartQuantityControl
        v-if="isInCart"
        :product-id="product.id"
        :max-quantity="product.stock"
        @update:quantity="handleQuantityUpdate"
      />
      <button
        v-else
        class="buy-button"
        :disabled="availableQuantity === 0"
        @click="handleAddToCart"
      >
        КУПИТЬ
      </button>
    </div>

    <!-- Модальное окно с информацией о товаре -->
    <ProductView
      v-if="isModalOpen"
      v-model:isOpen="isModalOpen"
      :product="product"
      @add-to-cart="handleAddToCart"
    />
  </div>
</template>
