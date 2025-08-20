import type { UUID } from "./common";
import type { ApiResponse } from "./api";

export interface ICartItem {
  id: UUID;
  product_id: UUID;
  quantity: number;
  price: number;
  subtotal: number;
  product_name: string;
  image_url: string | null;
}

export interface ICart {
  id: UUID;
  items: ICartItem[];
  total: number;
  expires_at: string;
  is_active: boolean;
}

export interface IAddToCartData {
  product_id: UUID;
  quantity: number;
}

export interface IUpdateCartItemData {
  quantity: number;
}

// export interface ICartResponse {
//   cart: ICart
//   message: string
// }

// export interface ApiResponse<T> {
//     message: string;
//     [key: string]: any;
//   }

export interface ICartResponse extends ApiResponse<ICart> {
  cart?: ICart;
}
