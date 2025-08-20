<script setup lang="ts">
import { useCheckout } from "@/composables/useCheckout.ts";
import { DeliveryMethod } from "@/types/order.ts";
import { logger } from "@/utils/logger.ts";

const { setDeliveryMethod: setDeliveryMethodCheckout, currentDeliveryMethod } = useCheckout();

const setDeliveryMethod = (method: DeliveryMethod) => {
  setDeliveryMethodCheckout(method);
  logger.debug("Delivery method changed", { method });
};
</script>

<template>
  <div class="delivery-toggle">
    <button
      class="toggle-btn left"
      :class="{ active: currentDeliveryMethod === DeliveryMethod.PICKUP }"
      @click="setDeliveryMethod(DeliveryMethod.PICKUP)"
    >
      <span class="toggle-btn-text">САМОВЫВОЗ</span>
    </button>
    <button
      class="toggle-btn right"
      :class="{ active: currentDeliveryMethod === DeliveryMethod.COURIER }"
      @click="setDeliveryMethod(DeliveryMethod.COURIER)"
    >
      <span class="toggle-btn-text">КУРЬЕР</span>
    </button>
  </div>
</template>

<style scoped>
.delivery-toggle {
  display: flex;
  justify-content: center;
  gap: 4px;
  margin: 0;
}

.toggle-btn {
  border: none;
  background: #252525;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

.toggle-btn.left {
  border-radius: 100px 0 0 100px;
}

.toggle-btn.right {
  border-radius: 0 100px 100px 0;
}

.toggle-btn.active {
  background: #ffb43d;
}

.toggle-btn-text {
  color: white;
  font-size: 8px;
  font-family: "Inter", sans-serif;
  font-weight: 700;
  line-height: 9.68px;
  letter-spacing: 0.08px;
  text-transform: uppercase;
}
</style>
