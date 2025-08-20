type LogType = "log" | "info" | "warn" | "error" | "debug"; // Добавили 'info'
type LogPayload = string | number | boolean | object | null | undefined | unknown;

interface LoggerConfig {
  apiUrl?: string;
  developmentMode?: boolean;
}

interface LogMessage {
  type: LogType;
  message: string;
  data?: Record<string, LogPayload>;
  user_id?: number; // Теперь это optional number без null
  context?: {
    url: string;
    userAgent: string;
    timestamp: string;
    isTelegramWebApp: boolean;
  };
}

export class AppLogger {
  private static instance: AppLogger;
  private readonly apiUrl: string;
  private readonly isDev: boolean;
  private userId?: number; // Изменили на optional number

  private constructor(config: LoggerConfig = {}) {
    this.apiUrl = config.apiUrl || import.meta.env.VITE_NGROK_URL || "http://localhost:8000";
    this.isDev = config.developmentMode ?? import.meta.env.DEV;
  }

  public static getInstance(config?: LoggerConfig): AppLogger {
    if (!AppLogger.instance) {
      AppLogger.instance = new AppLogger(config);
    }
    return AppLogger.instance;
  }

  public setUserId(id: number) {
    this.userId = id;
  }

  private async sendToServer(type: LogType, message: string, data?: Record<string, LogPayload>) {
    try {
      const payload: LogMessage = {
        type,
        message, // Теперь передаем просто строку
        data, // Дополнительные данные отдельно
        ...(this.userId && { user_id: this.userId }),
        context: {
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
          isTelegramWebApp: !!window.Telegram?.WebApp,
        },
      };

      // В development режиме используем dev-сервер
      if (this.isDev && window.location.hostname === "localhost") {
        try {
          await fetch("http://localhost:9229/log", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
        } catch (e) {
          console.error("Dev server log failed:", e);
        }
      }

      // Отправляем на основной бэкенд если не localhost
      if (window.location.hostname !== "localhost") {
        // await fetch(`${window.location.origin}/api/v1/debug/webapp-logs`, {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify(payload),
        //   credentials: 'include',
        // })
      }
    } catch (error) {
      if (this.isDev) {
        console.error("Failed to send log:", error);
      }
    }
  }

  // Добавили метод info
  public info(message: string, data?: Record<string, LogPayload>) {
    if (this.isDev || window.location.hostname === "localhost") {
      console.info(message, data || "");
    }
    void this.sendToServer("info", message, data);
  }

  public log(message: string, data?: Record<string, LogPayload>) {
    if (this.isDev || window.location.hostname === "localhost") {
      console.log(message, data || "");
    }
    void this.sendToServer("log", message, data);
  }

  public warn(message: string, data?: Record<string, LogPayload>) {
    if (this.isDev || window.location.hostname === "localhost") {
      console.warn(message, data || "");
    }
    void this.sendToServer("warn", message, data);
  }

  public debug(message: string, data?: Record<string, LogPayload>) {
    if (this.isDev || window.location.hostname === "localhost") {
      console.log(message, data || "");
    }
    void this.sendToServer("debug", message, data);
  }

  public error(message: string, data?: Record<string, LogPayload>) {
    if (this.isDev || window.location.hostname === "localhost") {
      console.error(message, data || "");
    }
    void this.sendToServer("error", message, data);
  }
}

export const logger = AppLogger.getInstance();
