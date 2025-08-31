import { defineStore } from "pinia";
import { ref, computed, watch } from "vue";
import type { ICreateOrder } from "@/types/order";
import { DeliveryMethod, PaymentMethod } from "@/types/order";
import type { IUserDeliveryPoint, IUserAddress } from "@/types/order";
import { orderService } from "@/services/orderService";
import { logger } from "@/utils/logger";
import { useUserStore } from "@/stores/user";
import { useNotification } from "@/composables/useNotification";
import { promoCodeService } from "@/services/promoCodeService";

const STORAGE_KEY_DELIVERY_METHOD = "checkout_delivery_method";
const STORAGE_KEY_PICKUP_POINT = "checkout_pickup_point";
const STORAGE_KEY_USER_ADDRESS = "checkout_user_address";
const STORAGE_KEY_PAYMENT_METHOD = "checkout_payment_method";

type PromoCodeStatus = "idle" | "loading" | "success" | "error";

export const useCheckoutStore = defineStore("checkout", () => {
  const isCheckoutActive = ref(false);
  const deliveryMethod = ref<DeliveryMethod | null>(null);
  const selectedPickupPoint = ref<IUserDeliveryPoint | null>(null);
  const selectedUserAddress = ref<IUserAddress | null>(null);
  const paymentMethod = ref<PaymentMethod | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  
  const promoCode = ref<string | null>(null);
  const discountPercent = ref(0);
  const promoCodeStatus = ref<PromoCodeStatus>("idle");
  const promoCodeMessage = ref("");

  const deliveryCost = ref<number | null>(null);
  const isCalculatingDelivery = ref(false);
  const { showNotification } = useNotification();
  const userStore = useUserStore();
  const userDiscountPercent = computed(() => userStore.discount?.current_percent || 0);

  const setPromoCode = (code: string | null, discount: number) => {
    promoCode.value = code;
    discountPercent.value = discount;
  };

  const applyPromoCode = async (code: string) => {
    if (!code.trim()) return;

    promoCodeStatus.value = "loading";
    promoCodeMessage.value = "";

    try {
      const response = await promoCodeService.applyPromoCode(code);
      if (response.is_valid) {
        setPromoCode(response.code, response.discount_percent);
        promoCodeStatus.value = "success";
        promoCodeMessage.value = "Промокод активирован!";
      } else {
        setPromoCode(null, 0);
        promoCodeStatus.value = "error";
        promoCodeMessage.value = "Неверный промокод!";
        setTimeout(() => {
          if (promoCodeStatus.value === 'error') {
            promoCodeStatus.value = "idle";
            promoCodeMessage.value = "";
          }
        }, 3000);
      }
    } catch (err) {
      logger.error("Failed to apply promo code", { code, error: err });
      setPromoCode(null, 0);
      promoCodeStatus.value = "error";
      promoCodeMessage.value = "Ошибка сервера";
      setTimeout(() => {
          if (promoCodeStatus.value === 'error') {
            promoCodeStatus.value = "idle";
            promoCodeMessage.value = "";
          }
      }, 3000);
    }
  };

  const removePromoCode = () => {
    setPromoCode(null, 0);
    promoCodeStatus.value = "idle";
    promoCodeMessage.value = "";
    showNotification("Промокод удален", "info");
  };

  
  const canProceed = computed(() => {
    return !!(
      deliveryMethod.value &&
      paymentMethod.value &&
      ((deliveryMethod.value === DeliveryMethod.PICKUP && selectedPickupPoint.value) ||
        (deliveryMethod.value === DeliveryMethod.COURIER && selectedUserAddress.value))
    );
  });

  const getDeliveryData = computed(() => {
    const isPickupSelected = deliveryMethod.value === DeliveryMethod.PICKUP;

    const deliveryPointId = isPickupSelected ? selectedPickupPoint.value?.id || "" : null;
    const addressId = !isPickupSelected ? selectedUserAddress.value?.id || "" : null;

    return {
      address_id: addressId,
      delivery_point_id: deliveryPointId,
    };
  });

  const calculateDeliveryCost = async () => {
    if (!deliveryMethod.value || 
       (deliveryMethod.value === DeliveryMethod.PICKUP && !selectedPickupPoint.value) ||
       (deliveryMethod.value === DeliveryMethod.COURIER && !selectedUserAddress.value)) 
    {
      deliveryCost.value = null;
      return;
    }
    
    isCalculatingDelivery.value = true;
    try {
        const orderData: ICreateOrder = {
            delivery_method: deliveryMethod.value,
            payment_method: PaymentMethod.YOOKASSA,
            address_id: deliveryMethod.value === DeliveryMethod.COURIER ? selectedUserAddress.value?.id : undefined,
            delivery_point_id: deliveryMethod.value === DeliveryMethod.PICKUP ? selectedPickupPoint.value?.id : undefined,
        };
        const tariff = await orderService.calculateDelivery(orderData);
        deliveryCost.value = tariff ? tariff.delivery_sum : null;
    } catch (e) {
        deliveryCost.value = null;
        logger.error("Delivery calculation failed in store", { error: e });
        showNotification(
            "Не удалось рассчитать доставку. Пожалуйста, выберите другой адрес.", 
            "error"
        );
    } finally {
        isCalculatingDelivery.value = false;
    }
  };

  const saveToLocalStorage = <T>(key: string, value: T | null): void => {
    try {
      if (value === null) {
        localStorage.removeItem(key);
      } else {
        localStorage.setItem(key, JSON.stringify(value));
      }
      logger.debug("Saved checkout data to localStorage", { key });
    } catch (err) {
      logger.error("Failed to save checkout data to localStorage", { key, error: err });
    }
  };

  const loadFromLocalStorage = <T>(key: string): T | null => {
    try {
      const value = localStorage.getItem(key);
      if (!value) return null;
      return JSON.parse(value) as T;
    } catch (err) {
      logger.error("Failed to load checkout data from localStorage", { key, error: err });
      return null;
    }
  };

  const loadSavedState = () => {
    try {
      const savedDeliveryMethod = loadFromLocalStorage<DeliveryMethod>(STORAGE_KEY_DELIVERY_METHOD);
      if (savedDeliveryMethod) {
        deliveryMethod.value = savedDeliveryMethod;
      }

      const savedPickupPoint = loadFromLocalStorage<IUserDeliveryPoint>(STORAGE_KEY_PICKUP_POINT);
      if (savedPickupPoint) {
        selectedPickupPoint.value = savedPickupPoint;
      }

      const savedUserAddress = loadFromLocalStorage<IUserAddress>(STORAGE_KEY_USER_ADDRESS);
      if (savedUserAddress) {
        selectedUserAddress.value = savedUserAddress;
      }

      const savedPaymentMethod = loadFromLocalStorage<PaymentMethod>(STORAGE_KEY_PAYMENT_METHOD);
      if (savedPaymentMethod) {
        paymentMethod.value = savedPaymentMethod;
      }

      logger.debug("Loaded checkout state from localStorage", {
        hasDeliveryMethod: !!savedDeliveryMethod,
        hasPickupPoint: !!savedPickupPoint,
        hasUserAddress: !!savedUserAddress,
        hasPaymentMethod: !!savedPaymentMethod,
      });
    } catch (err) {
      logger.error("Failed to load checkout state from localStorage", { error: err });
    }
  };

  watch(deliveryMethod, (newValue) => {
    saveToLocalStorage(STORAGE_KEY_DELIVERY_METHOD, newValue);
  });

  watch([deliveryMethod, selectedPickupPoint, selectedUserAddress], () => {
      calculateDeliveryCost();
  });

  watch(selectedPickupPoint, (newValue) => {
    saveToLocalStorage(STORAGE_KEY_PICKUP_POINT, newValue);
  });

  watch(selectedUserAddress, (newValue) => {
    saveToLocalStorage(STORAGE_KEY_USER_ADDRESS, newValue);
  });

  watch(paymentMethod, (newValue) => {
    saveToLocalStorage(STORAGE_KEY_PAYMENT_METHOD, newValue);
  });

  loadSavedState();

  const setDeliveryMethod = (method: DeliveryMethod) => {
    logger.debug("Setting delivery method", {
      oldMethod: deliveryMethod.value,
      newMethod: method,
    });
    deliveryMethod.value = method;
    saveToLocalStorage(STORAGE_KEY_DELIVERY_METHOD, method);
  };

  const setPickupPoint = (point: IUserDeliveryPoint) => {
    selectedPickupPoint.value = point;
    saveToLocalStorage(STORAGE_KEY_PICKUP_POINT, point);
    logger.debug("Pickup point selected", { pointId: point.id });
  };

  const setUserAddress = (address: IUserAddress) => {
    selectedUserAddress.value = address;
    saveToLocalStorage(STORAGE_KEY_USER_ADDRESS, address);
    logger.debug("User address selected", { addressId: address.id });
  };

  const setPaymentMethod = (method: PaymentMethod) => {
    paymentMethod.value = method;
    saveToLocalStorage(STORAGE_KEY_PAYMENT_METHOD, method);
    logger.debug("Payment method changed", { method });
  };

  const startCheckout = () => {
    isCheckoutActive.value = true;
    loadSavedState();
  };

  const finishCheckout = () => {
    isCheckoutActive.value = false;
  };

  const createOrder = async (orderData: ICreateOrder) => {
    try {
      if (!canProceed.value) {
        throw new Error("Cannot proceed with order - missing required fields");
      }

      isLoading.value = true;
      error.value = null;

      const response = await orderService.createOrder(orderData);
      logger.info("Order created successfully", { orderId: response.id });
      return response;
    } catch (err) {
      error.value = err instanceof Error ? err.message : "Failed to create order";
      logger.error("Failed to create order", { error: err });
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  const reset = () => {
    deliveryMethod.value = null;
    selectedPickupPoint.value = null;
    selectedUserAddress.value = null;
    paymentMethod.value = null;
    error.value = null;
    promoCode.value = null;
    discountPercent.value = 0;
    promoCodeStatus.value = 'idle';
    promoCodeMessage.value = '';

    saveToLocalStorage(STORAGE_KEY_DELIVERY_METHOD, null);
    saveToLocalStorage(STORAGE_KEY_PICKUP_POINT, null);
    saveToLocalStorage(STORAGE_KEY_USER_ADDRESS, null);
    saveToLocalStorage(STORAGE_KEY_PAYMENT_METHOD, null);

    logger.debug("Checkout state reset");
  };

  return {
    deliveryMethod,
    isCheckoutActive,
    selectedPickupPoint,
    selectedUserAddress,
    paymentMethod,
    isLoading,
    error,

    canProceed,
    getDeliveryData,
    userDiscountPercent,

    setDeliveryMethod,
    setPickupPoint,
    setUserAddress,
    setPaymentMethod,
    startCheckout,
    finishCheckout,
    createOrder,
    reset,
    loadSavedState,
    promoCode,
    discountPercent,
    setPromoCode,
    promoCodeStatus,
    promoCodeMessage,
    applyPromoCode,
    removePromoCode,
    deliveryCost,
    isCalculatingDelivery,
    calculateDeliveryCost,
  };
});