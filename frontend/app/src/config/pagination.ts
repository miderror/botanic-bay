/**
 * Настройки пагинации для административного интерфейса
 */
interface IPaginationConfig {
  /** Количество продуктов на странице в админке */
  ADMIN_PRODUCTS_PER_PAGE: number;

  /** Количество пользователей на странице в админке */
  ADMIN_USERS_PER_PAGE: number;

  /** Количество продуктов на странице в каталоге */
  CATALOG_PRODUCTS_PER_PAGE: number;

  /** Количество заказов на странице в админке */
  ADMIN_ORDERS_PER_PAGE: number;

  /** Количество заявок на вывод на странице в админке */
  ADMIN_PAYOUTS_PER_PAGE: number;
}

/**
 * Конфигурация пагинации для всего приложения
 */
export const paginationConfig: IPaginationConfig = {
  // Админка
  ADMIN_PRODUCTS_PER_PAGE: 5,
  ADMIN_USERS_PER_PAGE: 5,
  ADMIN_ORDERS_PER_PAGE: 5,
  ADMIN_PAYOUTS_PER_PAGE: 5,

  // Каталог
  CATALOG_PRODUCTS_PER_PAGE: 10,
} as const;

// Можно экспортировать отдельные значения для удобства
export const {
  ADMIN_PRODUCTS_PER_PAGE,
  ADMIN_USERS_PER_PAGE,
  CATALOG_PRODUCTS_PER_PAGE,
  ADMIN_ORDERS_PER_PAGE,
  ADMIN_PAYOUTS_PER_PAGE,
} = paginationConfig;
