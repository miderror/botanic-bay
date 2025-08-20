import type { LocationData } from "@/types/telegram.ts";

export interface TelegramWebApp {
  ready(): void;
  expand(): void;
  close(): void;
  showKeyboard: () => void;
  hideKeyboard: () => void;
  closeScanQrPopup: () => void;
  enableVerticalSwipes: () => void;
  disableVerticalSwipes: () => void;
  isVerticalSwipesEnabled: boolean;
  initDataUnsafe: {
    user?: {
      id: number;
      first_name: string;
      last_name?: string;
      username?: string;
      language_code?: string;
    };
    auth_date: number;
    hash: string;
  };
  themeParams: {
    button_color?: string;
    [key: string]: unknown;
  };
  LocationManager: ILocationManager;
  ContentSafeAreaInset: IContentSafeAreaInset;
}

interface ILocationManager {
  isInited: boolean;
  isLocationAvailable: boolean;
  isAccessRequested: boolean;
  isAccessGranted: boolean;
  init(callback?: () => void): void;
  getLocation(callback: (data?: LocationData | null) => void): void;
  openSettings(): void;
}

interface IContentSafeAreaInset {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}

export {}; // Чтобы файл считался модулем
