import { useProductQuantityStore } from "@/stores/productQuantityStore";
import { storeToRefs } from "pinia";
import { computed, onMounted, onUnmounted } from "vue";

export function useProductPolling(productId: string, customInterval?: number) {
  const store = useProductQuantityStore();
  const { isLoading, error } = storeToRefs(store);

  const availableQuantity = computed(() => store.getQuantity(productId));

  onMounted(() => {
    if (productId) {
      store.startPolling(productId, customInterval);
    }
  });

  onUnmounted(() => {
    if (productId) {
      store.stopPolling(productId);
    }
  });

  return {
    availableQuantity,
    isLoading,
    error,
  };
}
