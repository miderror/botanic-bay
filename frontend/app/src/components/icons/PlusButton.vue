<template>
  <svg
    width="28"
    height="28"
    viewBox="0 0 28 28"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      cx="14"
      cy="14"
      r="14"
      :fill="bgColor"
    />
    <rect
      x="7"
      y="13"
      width="14"
      height="2"
      fill="white"
    />
    <rect
      x="13"
      y="7"
      width="2"
      height="14"
      fill="white"
    />
  </svg>
</template>

<script setup lang="ts">
defineProps<{
  bgColor?: string;
}>();
</script>
