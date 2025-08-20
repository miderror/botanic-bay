<script setup lang="ts">
defineProps<{
  text: string;
  modelValue: boolean;
}>();

defineEmits(["update:modelValue"]);
</script>

<template>
  <div class="flex items-center justify-between w-full">
    <p>{{ text }}</p>
    <label class="toggle">
      <input
        type="checkbox"
        :checked="modelValue"
        @change="$emit('update:modelValue', $event.target.checked)"
      />
      <span class="slider"></span>
    </label>
  </div>
</template>

<style scoped>
p {
  font-family: "Inter", sans-serif;
  font-size: 8px;
  font-weight: 700;
}

.toggle {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 28px;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: white;
  transition: 0.4s;
  border-radius: 24px;
}

.slider::before {
  position: absolute;
  content: "";
  height: 22px;
  width: 22px;
  left: 3px;
  top: 3px;

  background-color: #dad8d7;
  transition: 0.4s;
  border-radius: 50%;
}

input:checked + .slider::before {
  background-color: #66ca1a;
}

input:checked + .slider::before {
  transform: translateX(22px);
}
</style>
