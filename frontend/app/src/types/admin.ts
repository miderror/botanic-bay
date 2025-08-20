import type { IReferralPayoutRequest } from "@/types/business.ts";
import type { IOrder } from "./order";
import type { IProduct } from "./product";
import type { IUser } from "./user";

// Фильтры
export interface IAdminProductFilter {
  name?: string;
  category?: string;
  is_active?: boolean;
}

export interface IAdminUserFilter {
  username?: string;
  telegram_id?: number;
  role?: string;
  is_active?: boolean;
}

// Расширенные модели для админки
export interface IAdminProduct extends IProduct {
  total_orders: number;
  last_ordered_at: string | null;
}

export interface IAdminUser extends IUser {
  total_orders: number;
  total_spent: number;
  last_order_at: string | null;
  roles: string[];
}

// Ответы от API с пагинацией
export interface IPaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface IAdminOrderFilter {
  order_id?: string;
  status?: string;
  from_date?: string;
  to_date?: string;
  min_total?: number;
  max_total?: number;
}

export interface IAdminOrderList {
  items: IOrder[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface IAdminPayoutList {
  items: IReferralPayoutRequest[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface IOrderStats {
  total_count: number;
  total_revenue: number;
  average_order_value: number;
  status_counts: Record<string, number>;
}

// Добавим в интерфейс фильтров возможность поиска по пользователю
export interface IAdminOrderFilter {
  orderId?: string;
  status?: string;
  fromDate?: string;
  toDate?: string;
  minTotal?: number;
  maxTotal?: number;
  userId?: string;
  userFullName?: string; // Для поиска по имени пользователя
}

export interface IAdminPayoutFilter {
  id?: string;
  status?: string;
  fromDate?: string;
  toDate?: string;
}

// Перечисление форматов экспорта
export enum ExportFormat {
  CSV = "csv",
  EXCEL = "excel",
}

// Интерфейс для запроса экспорта
export interface IExportOrdersRequest {
  format: ExportFormat;
  filters?: IAdminOrderFilter;
}
