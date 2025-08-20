import type { IProduct, IProductListResponse } from "@/types/product";
import { logger } from "@/utils/logger";

export class ProductService {
  private baseUrl: string;

  constructor(baseUrl: string = "/api/v1") {
    this.baseUrl = baseUrl;
  }

  async getAvailableQuantity(productId: string): Promise<number> {
    // logger.debug('Getting available quantity', { productId })
    try {
      const response = await fetch(`${this.baseUrl}/products/${productId}/available-quantity`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      logger.error("Failed to fetch available quantity", { error, productId });
      throw error;
    }
  }

  // Добавляем метод getCategories в productService
  async getCategories(): Promise<string[]> {
    try {
      logger.info("Fetching all product categories");

      // Делаем запрос к API для получения всех категорий
      const response = await fetch(`${this.baseUrl}/products/categories`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      logger.info("Categories fetched successfully", { count: data.categories?.length });

      return data.categories || [];
    } catch (error) {
      logger.error("Failed to fetch categories", { error });
      throw error;
    }
  }

  async getProducts(page: number = 1, limit: number = 10, category?: string): Promise<IProductListResponse> {
    try {
      const skip = (page - 1) * limit;
      let url = `${this.baseUrl}/products?skip=${skip}&limit=${limit}`;

      if (category) {
        url += `&category=${encodeURIComponent(category)}`;
      }

      logger.info("API request", {
        url,
        page,
        limit,
        category,
        skip,
      });

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      logger.info("API response", {
        itemsReceived: data.items?.length,
        total: data.total,
        pages: data.pages,
      });

      return data as IProductListResponse;
    } catch (error) {
      logger.error("Failed to fetch products", { error });
      throw error;
    }
  }

  async getProduct(id: string): Promise<IProduct> {
    try {
      logger.info("Fetching product details", { productId: id });

      const response = await fetch(`${this.baseUrl}/products/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data as IProduct;
    } catch (error) {
      logger.error("Failed to fetch product details", { error, productId: id });
      throw error;
    }
  }

  async searchProducts(query: string): Promise<IProductListResponse> {
    try {
      const url = `${this.baseUrl}/products/search?q=${encodeURIComponent(query)}`;

      logger.info("Search request", { query });

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      logger.info("Search response", {
        itemsFound: data.items?.length,
        total: data.total,
      });

      return data as IProductListResponse;
    } catch (error) {
      logger.error("Search request failed", { error, query });
      throw error;
    }
  }
}

// Создаем экземпляр сервиса для использования в компонентах
export const productService = new ProductService();
