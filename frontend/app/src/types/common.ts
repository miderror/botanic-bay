/**
 * Тип для UUID строк
 */
export type UUID = string;

/**
 * Общие типы для API ответов
 */
export interface ApiResponse<T> {
  message: string;
  data?: T;
  [key: string]: unknown;
}
