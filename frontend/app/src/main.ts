import "@/assets/base.css";
import "@/assets/main.css";
import { createPinia } from "pinia";
import { createApp } from "vue";
import { RecycleScroller } from "vue-virtual-scroller";
import "vue-virtual-scroller/dist/vue-virtual-scroller.css";
import { createYmaps } from "vue-yandex-maps";
import App from "./App.vue";
import "./assets/fonts/fonts.css";
import router from "./router";
import "./utils/logger";

// Функция установки реальной высоты viewport
const setRealVh = () => {
  document.documentElement.style.setProperty("--real-vh", `${window.innerHeight}px`);
};

// Проверяем загрузку шрифтов
document.fonts.ready
  .then(() => {
    document.body.classList.add("fonts-loaded");
    console.log("🥡 Все шрифты загружены");
  })
  .catch((error) => {
    console.error("🥡 Ошибка при загрузке шрифтов:", error);
  });

// Устанавливаем начальную высоту
setRealVh();

// Обработчик изменения размера окна с debounce
let resizeTimeout: number | null = null;
window.addEventListener("resize", () => {
  if (resizeTimeout) {
    window.cancelAnimationFrame(resizeTimeout);
  }
  resizeTimeout = window.requestAnimationFrame(setRealVh);
});

const app = createApp(App);
app.use(createPinia());
app.use(router);

app.component("RecycleScroller", RecycleScroller);

const yandexMapsApiKey = import.meta.env.VITE_YANDEX_MAPS_API_KEY;
console.log("Yandex Maps API Key:", yandexMapsApiKey);
app.use(
  createYmaps({
    apikey: yandexMapsApiKey,
  }),
);

// Глобальный обработчик ошибок
window.addEventListener("error", (event) => {
  console.error("❌ Global error:", {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error,
    stack: event.error?.stack,
  });
});

// Обработчик необработанных промисов
window.addEventListener("unhandledrejection", (event) => {
  console.error("❌ Unhandled promise rejection:", {
    reason: event.reason,
    promise: event.promise,
  });
});

// Обработчик ошибок Vue
app.config.errorHandler = (err, instance, info) => {
  console.error("❌ Vue error:", {
    error: err,
    instance,
    info,
    stack: (err as Error)?.stack,
  });
};

app.mount("#app");
