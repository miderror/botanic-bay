import { ref } from "vue";

export function useNotification() {
  const message = ref("");
  const type = ref<"success" | "error" | "info">("info");
  const show = ref(false);
  let timeout: NodeJS.Timeout;

  const showNotification = (
    msg: string,
    notificationType: "success" | "error" | "info" = "info",
    duration: number = 3000,
  ) => {
    // Очищаем предыдущий таймаут если есть
    if (timeout) clearTimeout(timeout);

    message.value = msg;
    type.value = notificationType;
    show.value = true;

    timeout = setTimeout(() => {
      show.value = false;
    }, duration);
  };

  return {
    message,
    type,
    show,
    showNotification,
  };
}
