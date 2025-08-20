interface Config {
  telegramBotName: string;
  maxAdditionalProductImages: number;
  polling: {
    enabled: boolean;
    interval: number; // в миллисекундах
    productQuantity: boolean; // отдельный флаг для доступности товаров
  };
}

const config: Config = {
  telegramBotName: import.meta.env.VITE_TELEGRAM_BOT_NAME || "YourBotName",
  maxAdditionalProductImages: 5,
  polling: {
    enabled: true, // глобальное включение/выключение
    interval: 10000, // 10 секунд по умолчанию
    productQuantity: true, // включен ли polling для количества товаров
  },
};

export default config;
