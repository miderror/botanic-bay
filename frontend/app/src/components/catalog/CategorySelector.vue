<script setup lang="ts">
defineProps<{
  categories: string[];
  selectedCategory: string;
}>();

defineEmits<{
  (e: "select", category: string): void;
}>();
</script>

<template>
  <div class="category-selector">
    <div
      class="categories-scroll"
      ref="scrollContainer"
    >
      <button
        v-for="(category, index) in categories"
        :key="category"
        class="category-btn"
        :class="{
          active: selectedCategory === category,
          'first-btn': index === 0,
          'last-btn': index === categories.length - 1,
        }"
        @click="$emit('select', category)"
      >
        <span :title="category">{{ category }}</span>
      </button>
    </div>
  </div>
</template>
