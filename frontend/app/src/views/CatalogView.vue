<script setup lang="ts">
import ProductList from "@/components/catalog/ProductList.vue";
import { useCart } from "@/composables/useCart";
import { onMounted } from "vue";

const { cart, initCart } = useCart();

onMounted(async () => {
  if (!cart.value) {
    await initCart();
  }
});
</script>

<template>
  <div class="catalog">
    <div class="catalog-background"></div>
    <ProductList />
  </div>
</template>

<style>
@import "@/assets/styles/catalog.css";
</style>
