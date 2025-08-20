export interface IProduct {
  id: string;
  name: string;
  description: string;
  additional_description: string | null;
  price: number;
  stock: number;
  isActive: boolean;
  category: string;
  image_url: string | null;
  background_image_url: string | null;
  additional_images_urls?: string[]; // Добавляем поле для дополнительных изображений
  sku: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface IProductListResponse {
  items: IProduct[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
