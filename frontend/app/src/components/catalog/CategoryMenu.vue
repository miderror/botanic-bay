<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";

const props = defineProps<{
  categories: string[];
  selectedCategory: string;
}>();

const emit = defineEmits<{
  (e: "select", category: string): void;
}>();

const isDropdownOpen = ref(false);
const menuRef = ref<HTMLElement | null>(null);

const leftButtonText = computed(() => {
  return props.selectedCategory || "ВСЕ ТОВАРЫ";
});

const displayCategories = computed(() => {
  return ["ВСЕ ТОВАРЫ", ...props.categories];
});

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value;
};

const selectCategory = (category: string) => {
  const categoryToEmit = category === "ВСЕ ТОВАРЫ" ? "" : category;
  emit("select", categoryToEmit);
  isDropdownOpen.value = false;
};

const handleClickOutside = (event: MouseEvent) => {
  if (menuRef.value && !menuRef.value.contains(event.target as Node)) {
    isDropdownOpen.value = false;
  }
};

onMounted(() => {
  document.addEventListener("click", handleClickOutside, true);
});

onUnmounted(() => {
  document.removeEventListener("click", handleClickOutside, true);
});
</script>

<template>
  <div
    class="category-menu"
    ref="menuRef"
  >
    <div
      v-if="!isDropdownOpen"
      class="menu-buttons"
    >
      <button class="menu-btn left active">
        <span>{{ leftButtonText }}</span>
      </button>
      <button
        class="menu-btn right"
        @click.stop="toggleDropdown"
      >
        <span>РАЗДЕЛ</span>
      </button>
    </div>

    <Transition name="dropdown-fade">
      <div
        v-if="isDropdownOpen"
        class="dropdown-panel"
      >
        <button
          v-for="category in displayCategories"
          :key="category"
          class="dropdown-item"
          :class="{ active: category === selectedCategory || (category === 'ВСЕ ТОВАРЫ' && !selectedCategory) }"
          @click="selectCategory(category)"
        >
          {{ category }}
        </button>
      </div>
    </Transition>
  </div>
</template>