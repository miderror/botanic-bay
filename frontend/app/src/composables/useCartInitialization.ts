import { ref } from "vue";

const isInitialized = ref(false);

export function useCartInitialization() {
  return {
    isInitialized,
  };
}
