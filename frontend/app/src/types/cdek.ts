import type { UUID } from "./common";

export enum OfficeType {
  POSTAMAT = "POSTAMAT",
  PVZ = "PVZ",
  ALL = "ALL",
}

export interface IOfficeLocation {
  country_code: string;
  region_code: string;
  region: string;
  city_code: string;
  city: string;
  longitude: number;
  latitude: number;
  address: string;
  address_full: string;
}

export interface IDeliveryPoint {
  uuid: UUID;
  code: string;
  location: IOfficeLocation;
  work_time: string;
  type: OfficeType;
}

export interface IAddress {
  address: string;
  address_full?: string;
  latitude: number;
  longitude: number;
}

// Интерфейсы для поиска адресов
export interface IAddressSearchParams {
  query: string;
  user_latitude?: number;
  user_longitude?: number;
  limit?: number;
}

export interface IDeliveryPointSearchParams {
  address_query: string;
  user_latitude?: number;
  user_longitude?: number;
  limit?: number;
}

export interface IAddressSearchResult {
  id: string;
  title: string;
  subtitle: string;
  full_address: string;
  country: string | null;
  city: string | null;
  street: string | null;
  house: string | null;
  latitude: number;
  longitude: number;
  distance_km?: number;
}

export interface IDeliveryPointSearchResult {
  id: string;
  title: string;
  subtitle: string;
  address: string;
  latitude: number;
  longitude: number;
  distance_km?: number;
  work_time: string;
  office_type: string;
}
