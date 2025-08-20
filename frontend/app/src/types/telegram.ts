export interface TelegramUser {
  id: number;
  username?: string;
  first_name: string;
  last_name?: string;
}

export interface TelegramWebAppData {
  user?: TelegramUser;
  auth_date: number;
  hash: string;
}

export interface LocationData {
  latitude: number; // Широта (в градусах)
  longitude: number; // Долгота (в градусах)
  altitude: number | null; // Высота над уровнем моря (в метрах) или null
  course: number | null; // Направление движения (0 = North, 90 = East, ...) или null
  speed: number | null; // Скорость устройства в м/с или null
  horizontal_accuracy: number | null; // Точность координат (в метрах) или null
  vertical_accuracy: number | null; // Точность данных по высоте (в метрах) или null
  course_accuracy: number | null; // Точность данных по курсу (в градусах) или null
  speed_accuracy: number | null; // Точность данных по скорости (в м/с) или null
}
