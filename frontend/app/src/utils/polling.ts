import config from "@/config";
import { logger } from "@/utils/logger";

export const polling = {
  enable() {
    config.polling.enabled = true;
    logger.info("Global polling enabled");
  },

  disable() {
    config.polling.enabled = false;
    logger.info("Global polling disabled");
  },

  enableProductQuantity() {
    config.polling.productQuantity = true;
    logger.info("Product quantity polling enabled");
  },

  disableProductQuantity() {
    config.polling.productQuantity = false;
    logger.info("Product quantity polling disabled");
  },

  setInterval(ms: number) {
    config.polling.interval = ms;
    logger.info("Polling interval updated", { interval: ms });
  },
};
