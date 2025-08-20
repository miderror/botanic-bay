// Настройка глобальных переменных для тестов
import { beforeAll, vi } from "vitest";

beforeAll(() => {
  // Мокаем Telegram WebApp API, если он используется
  Object.defineProperty(window, "Telegram", {
    value: {
      WebApp: {
        ready: vi.fn(),
        expand: vi.fn(),
        close: vi.fn(),
        MainButton: {
          setText: vi.fn(),
          show: vi.fn(),
          hide: vi.fn(),
          onClick: vi.fn(),
        },
        BackButton: {
          show: vi.fn(),
          hide: vi.fn(),
          onClick: vi.fn(),
        },
        initData: "",
        initDataUnsafe: {},
        themeParams: {},
      },
    },
    writable: true,
  });
});
