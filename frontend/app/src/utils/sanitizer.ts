import { SEARCH_VALIDATION } from "@/constants/validation";
import { logger } from "@/utils/logger";

export function sanitizeSearchQuery(query: string): string {
  try {
    // Удаляем пробелы ТОЛЬКО В НАЧАЛЕ строки
    let sanitized = query.replace(/^\s+/, "");

    // Удаляем запрещенные символы, не трогая пробелы
    const forbiddenCharsPattern = /[^a-zA-Zа-яА-Я0-9\s*.,!?()-]/g;
    if (forbiddenCharsPattern.test(sanitized)) {
      sanitized = sanitized.replace(forbiddenCharsPattern, "");
      logger.warn("Search query contained forbidden characters", {
        original: query,
        sanitized,
      });
    }

    // Заменяем множественные пробелы на один пробел
    sanitized = sanitized.replace(/\s{2,}/g, " ");

    if (sanitized.length > SEARCH_VALIDATION.MAX_LENGTH) {
      sanitized = sanitized.substring(0, SEARCH_VALIDATION.MAX_LENGTH);
      logger.warn("Search query was truncated to max length", {
        original: query,
        sanitized,
      });
    }

    return sanitized;
  } catch (error) {
    logger.error("Error while sanitizing search query", { error });
    return "";
  }
}
