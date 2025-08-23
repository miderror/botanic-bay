import { apiClient } from "./httpClient";
import { logger } from "@/utils/logger";
import type { IPromoCodeApplyResponse } from "@/types/promo_code";

class PromoCodeService {
  async applyPromoCode(code: string): Promise<IPromoCodeApplyResponse> {
    try {
      logger.info("Applying promo code", { code });
      const response = await apiClient.post<IPromoCodeApplyResponse>("/promo-codes/apply", { code });
      return response;
    } catch (error) {
      logger.error("Failed to apply promo code", { code, error });
      throw error;
    }
  }
}

export const promoCodeService = new PromoCodeService();