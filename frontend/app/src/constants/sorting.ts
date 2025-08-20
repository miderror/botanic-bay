/**
 * Константы для сортировки партнеров
 */

export const SORT_TYPES = {
  HIGHEST_BONUS: "Больший бонус",
  NEWEST: "Новые",
} as const;

export const SORT_TYPE_OPTIONS = [SORT_TYPES.HIGHEST_BONUS, SORT_TYPES.NEWEST] as const;

export const DEFAULT_SORT_TYPE = SORT_TYPES.HIGHEST_BONUS;

export type SortType = (typeof SORT_TYPES)[keyof typeof SORT_TYPES];
