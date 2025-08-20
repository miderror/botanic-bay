export enum UserDiscountLevel {
  NONE = "NONE",
  BRONZE = "BRONZE",
  SILVER = "SILVER",
  GOLD = "GOLD",
}

export interface IUser {
  id: string;
  telegram_id: number;
  username?: string;
  full_name: string;
  roles: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface IUserProfile {
  full_name: string | null;
  phone_number: string | null;
  email: string | null;
}

export interface IUserDiscount {
  current_percent: number;
  current_level: UserDiscountLevel;
  current_total: number;
  required_total: number;
  amount_left: number;
  next_level: UserDiscountLevel;
  next_percent: number;
}

export interface IUserMonthlyOrders {
  monthly_orders_amount: number;
}
