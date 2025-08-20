import type { ComputedRef } from "vue";
import { computed, ref, watch } from "vue";

export function useEditableField(
  modelValue: ComputedRef<string | null | undefined>,
  options?: {
    validator?: (val: string) => boolean;
  },
) {
  const input = ref(modelValue.value ?? "");
  const validator = options?.validator ?? (() => true);

  watch(modelValue, (val) => {
    input.value = val ?? "";
  });

  const isSaved = computed(() => input.value === modelValue.value);
  const isValid = computed(() => validator(input.value));
  const showSave = computed(() => {
    const trimmed = input.value.trim();
    return trimmed.length > 0 && !isSaved.value && isValid.value;
  });

  return { input, isSaved, isValid, showSave };
}
