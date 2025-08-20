import { logger } from "@/utils/logger";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

export function useViewport() {
  // Базовые метрики viewport
  const width = ref(0);
  const height = ref(0);
  const viewportHeight = ref(0);
  const isKeyboardVisible = ref(false);
  const keyboardHeight = ref(0);

  // Вычисляем реальную высоту viewport
  const realVh = computed(() => {
    return viewportHeight.value;
  });

  // Проверяем поддержку Visual Viewport API
  const hasVisualViewport = typeof window !== "undefined" && "visualViewport" in window;

  // Основная функция обновления метрик viewport
  const updateViewportMetrics = () => {
    const previousHeight = viewportHeight.value;
    const previousKeyboardHeight = keyboardHeight.value;

    // Обновляем базовые размеры
    width.value = window.innerWidth;
    height.value = window.innerHeight;

    // Определяем актуальную высоту viewport
    const newHeight = hasVisualViewport ? window.visualViewport!.height : window.innerHeight;

    // Проверяем существенность изменения высоты
    const heightDiff = Math.abs(window.innerHeight - newHeight);
    const isKeyboard = heightDiff > 150;

    // Обновляем состояние только при существенных изменениях
    if (Math.abs(previousHeight - newHeight) > 50 || isKeyboard !== isKeyboardVisible.value) {
      viewportHeight.value = newHeight;
      isKeyboardVisible.value = isKeyboard;
      keyboardHeight.value = isKeyboard ? heightDiff : 0;

      const navHeight =
        parseInt(getComputedStyle(document.documentElement).getPropertyValue("--nav-height")) || 0;

      const safeKeyboardPadding = isKeyboardVisible.value
        ? `${keyboardHeight.value - navHeight}px`
        : `${navHeight}px`;

      // Обновляем CSS переменные с проверками
      try {
        if (document.documentElement && typeof document.documentElement.style.setProperty === "function") {
          document.documentElement.style.setProperty("--real-vh", `${newHeight}px`);
          document.documentElement.style.setProperty("--keyboard-height", `${keyboardHeight.value}px`);
          document.documentElement.style.setProperty("--safe-keyboard-padding", safeKeyboardPadding);
        }
      } catch (error) {
        logger.error("updateViewportMetrics: не удалось обновить переменные CSS", { error });
      }

      // Логируем существенные изменения
      logger.debug("Viewport metrics updated", {
        width: width.value,
        height: height.value,
        newViewportHeight: newHeight,
        previousViewportHeight: previousHeight,
        isKeyboardVisible: isKeyboardVisible.value,
        keyboardHeight: keyboardHeight.value,
        heightDiff,
        previousKeyboardHeight,
      });
    }
  };

  // Используем requestAnimationFrame для оптимизации производительности
  let resizeTimeout: number | null = null;

  const debouncedUpdate = () => {
    if (resizeTimeout) {
      window.cancelAnimationFrame(resizeTimeout);
    }
    resizeTimeout = window.requestAnimationFrame(updateViewportMetrics);
  };

  // Инициализация при монтировании компонента
  onMounted(() => {
    // Выполняем начальное обновление
    updateViewportMetrics();

    // Добавляем слушатели событий
    if (hasVisualViewport) {
      // Используем Visual Viewport API если доступен
      window.visualViewport!.addEventListener("resize", debouncedUpdate);
      window.visualViewport!.addEventListener("scroll", debouncedUpdate);

      // Дополнительно слушаем window resize для надежности
      window.addEventListener("resize", debouncedUpdate);

      logger.debug("Visual Viewport API listeners attached");
    } else {
      // Fallback на стандартные события window
      window.addEventListener("resize", debouncedUpdate);
      logger.debug("Standard window resize listener attached");
    }
  });

  // Очистка при размонтировании компонента
  onUnmounted(() => {
    // Удаляем все слушатели событий
    if (hasVisualViewport) {
      window.visualViewport!.removeEventListener("resize", debouncedUpdate);
      window.visualViewport!.removeEventListener("scroll", debouncedUpdate);
    }

    window.removeEventListener("resize", debouncedUpdate);

    // Отменяем отложенное обновление если есть
    if (resizeTimeout) {
      window.cancelAnimationFrame(resizeTimeout);
      resizeTimeout = null;
    }

    logger.debug("Viewport listeners cleaned up");
  });

  // Отслеживаем изменение состояния клавиатуры
  watch(isKeyboardVisible, (visible) => {
    document.documentElement.style.setProperty("--keyboard-visible", visible ? "1" : "0");

    logger.debug("Keyboard visibility CSS variable updated", {
      visible,
      cssValue: visible ? "1" : "0",
    });
  });

  // Возвращаем публичное API composable
  return {
    // Базовые метрики
    width, // Ширина окна
    height, // Высота окна
    viewportHeight, // Текущая высота viewport
    realVh, // Вычисляемая реальная высота
    isKeyboardVisible, // Флаг видимости клавиатуры
    keyboardHeight, // Высота клавиатуры
  };
}
