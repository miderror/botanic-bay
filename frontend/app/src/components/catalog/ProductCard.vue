<script setup lang="ts">
import CartQuantityControl from "@/components/cart/CartQuantityControl.vue";
import ProductView from "@/components/product/ProductView.vue";
import { useCart } from "@/composables/useCart";
import { useImageUrl } from "@/composables/useImageUrl";
import { useProductPolling } from "@/composables/useProductPolling";
import type { IProduct } from "@/types/product";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import { computed, ref } from "vue";

const props = defineProps<{
  product: IProduct;
}>();

const { getImageUrl, handleImageError } = useImageUrl();
const { cart, addToCart } = useCart();
const { availableQuantity } = useProductPolling(props.product.id);

const isModalOpen = ref(false);

const isInCart = computed(() => {
  return cart.value?.items.some((item) => item.product_id === props.product.id);
});

const imageUrl = computed(() => getImageUrl(props.product.image_url));

const showProductDetails = () => {
  isModalOpen.value = true;
};

const handleAddToCart = async () => {
  await addToCart(props.product.id, 1);
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
      <div class="product-stock">В наличии {{ availableQuantity ?? product.stock }} шт.</div>
    </div>

    <div class="product-controls">
      <CartQuantityControl
        v-if="isInCart"
        :product-id="product.id"
        :max-quantity="product.stock"
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

    <ProductView
      v-if="isModalOpen"
      v-model:isOpen="isModalOpen"
      :product="product"
      @add-to-cart="handleAddToCart"
    />
  </div>
</template>