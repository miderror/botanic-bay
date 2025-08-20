import { logger } from "@/utils/logger";

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  responseType?: "json" | "blob" | "text";
}

export class HttpClient {
  private basePath: string;

  constructor(basePath: string) {
    this.basePath = basePath;
  }

  /**
   * Получение заголовков для Telegram WebApp
   * Требуется для аутентификации пользователя на бэкенде
   */
  private getTelegramHeaders(): Record<string, string> {
    const webApp = window.Telegram?.WebApp;
    if (!webApp) {
      logger.warn("Telegram WebApp is not available");
      return {};
    }

    const headers: Record<string, string> = {
      "X-Telegram-Init-Data": webApp.initData || "",
    };

    if (webApp.initDataUnsafe?.user?.id) {
      headers["X-Telegram-User-Id"] = webApp.initDataUnsafe.user.id.toString();
    }

    return headers;
  }

  /**
   * Формирование URL с параметрами запроса
   * @param endpoint - конечная точка API
   * @param params - параметры запроса
   */
  private buildUrl(endpoint: string, params?: Record<string, string | number | boolean | undefined>): string {
    // Используем URLSearchParams для безопасного построения query string
    const searchParams = new URLSearchParams();

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          searchParams.append(key, String(value));
        }
      });
    }

    // Формируем относительный путь (будет работать с настроенным прокси в vite)
    const path = `${this.basePath}${endpoint}`;
    const queryString = searchParams.toString();

    return queryString ? `${path}?${queryString}` : path;
  }

  /**
   * Базовый метод для выполнения HTTP запросов
   * @param endpoint - конечная точка API
   * @param options - параметры запроса
   */
  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    try {
      const { params, responseType, ...requestOptions } = options;

      const url = this.buildUrl(endpoint, params);

      logger.info("Making request", {
        url,
        method: options.method || "GET",
        responseType: responseType || "json",
      });

      // Объединяем пользовательские заголовки с Telegram заголовками
      const headers = {
        "Content-Type": "application/json",
        ...this.getTelegramHeaders(),
        ...options.headers,
      };

      const response = await fetch(url, {
        ...requestOptions,
        headers,
        credentials: "include", // Важно для работы с куками
      });

      if (!response.ok) {
        // Если запрос на получение blob или text, возвращаем общую ошибку
        if (responseType === "blob" || responseType === "text") {
          throw new Error(`HTTP error! status: ${response.status} ${response.statusText}`);
        }

        // Для обычных запросов пробуем получить детали ошибки из JSON
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `HTTP error! status: ${response.status} ${response.statusText}`);
      }

      // Для DELETE запросов возвращаем undefined без попытки распарсить JSON
      if (response.status === 204) {
        return undefined as T;
      }

      // Возвращаем данные в соответствии с запрошенным типом
      if (responseType === "blob") {
        return (await response.blob()) as unknown as T;
      } else if (responseType === "text") {
        return (await response.text()) as unknown as T;
      } else {
        // По умолчанию парсим как JSON
        return (await response.json()) as T;
      }
    } catch (error) {
      logger.error("HTTP request failed", {
        error,
        endpoint,
        options,
      });
      throw error;
    }
  }

  /**
   * GET запрос
   * @param endpoint - конечная точка API
   * @param params - параметры запроса для query string
   */
  async get<T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
    return this.request<T>(endpoint, { params });
  }

  /**
   * POST запрос
   * @param endpoint - конечная точка API
   * @param data - данные для отправки в теле запроса
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async post<T>(endpoint: string, data?: any): Promise<T>;
  /**
   * POST запрос с расширенными опциями
   * @param endpoint - конечная точка API
   * @param data - данные для отправки в теле запроса
   * @param options - дополнительные опции запроса (responseType, headers, params)
   */
  async post<T>(
    endpoint: string,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    data?: any,
    options?: {
      responseType?: "json" | "blob" | "text";
      headers?: Record<string, string>;
      params?: Record<string, string | number | boolean | undefined>;
    },
  ): Promise<T>;
  async post<T>(
    endpoint: string,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    data?: any,
    options?: {
      responseType?: "json" | "blob" | "text";
      headers?: Record<string, string>;
      params?: Record<string, string | number | boolean | undefined>;
    },
  ): Promise<T> {
    return this.request<T>(endpoint, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
      responseType: options?.responseType,
      headers: options?.headers,
      params: options?.params,
    });
  }

  /**
   * PATCH запрос
   * @param endpoint - конечная точка API
   * @param data - данные для отправки в теле запроса
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  /**
   * DELETE запрос
   * @param endpoint - конечная точка API
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async delete<T = any>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }

  /**
   * Загрузка файла
   * @param endpoint - конечная точка API
   * @param file - файл для загрузки
   * @returns - данные о загруженном файле
   * @throws - если не удалось загрузить файл
   */
  async uploadFile<T>(endpoint: string, file: File): Promise<T> {
    const formData = new FormData();
    formData.append("file", file);

    // Берем только Telegram заголовки, не добавляя Content-Type
    const telegramHeaders = {
      "X-Telegram-Init-Data": window.Telegram?.WebApp?.initData || "",
      "X-Telegram-User-Id": window.Telegram?.WebApp?.initDataUnsafe?.user?.id?.toString() || "",
    };

    try {
      logger.info("Making file upload request", {
        url: `${this.basePath}${endpoint}`,
        method: "POST",
        fileSize: file.size,
        fileType: file.type,
      });

      const response = await fetch(`${this.basePath}${endpoint}`, {
        method: "POST",
        body: formData,
        headers: telegramHeaders,
        credentials: "include",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `HTTP error! status: ${response.status} ${response.statusText}`);
      }

      return (await response.json()) as T;
    } catch (error) {
      logger.error("HTTP file upload request failed", {
        error,
        endpoint,
      });
      throw error;
    }
  }
}

// Создаем и экспортируем экземпляр для API
export const apiClient = new HttpClient("/api/v1");
