import { defineStore } from "pinia";
import { ref, computed, watch } from "vue";
import type { ICreateOrder } from "@/types/order";
import { DeliveryMethod, PaymentMethod } from "@/types/order";
import type { IUserDeliveryPoint, IUserAddress } from "@/types/order";
import { orderService } from "@/services/orderService";
import { logger } from "@/utils/logger";

// Константы для ключей localStorage
const STORAGE_KEY_DELIVERY_METHOD = "checkout_delivery_method";
const STORAGE_KEY_PICKUP_POINT = "checkout_pickup_point";
const STORAGE_KEY_USER_ADDRESS = "checkout_user_address";
const STORAGE_KEY_PAYMENT_METHOD = "checkout_payment_method";

export const useCheckoutStore = defineStore("checkout", () => {
  // Состояние
  const isCheckoutActive = ref(false);
  const deliveryMethod = ref<DeliveryMethod | null>(null);
  const selectedPickupPoint = ref<IUserDeliveryPoint | null>(null);
  const selectedUserAddress = ref<IUserAddress | null>(null);
  const paymentMethod = ref<PaymentMethod | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Вычисляемые свойства
  const canProceed = computed(() => {
    return !!(
      deliveryMethod.value &&
      paymentMethod.value &&
      ((deliveryMethod.value === DeliveryMethod.PICKUP && selectedPickupPoint.value) ||
        (deliveryMethod.value === DeliveryMethod.COURIER && selectedUserAddress.value))
    );
  });

  // Получение текущего адреса в зависимости от метода доставки
  const getDeliveryData = computed(() => {
    const isPickupSelected = currentDeliveryMethod.value === DeliveryMethod.PICKUP;

    const deliveryPointId = isPickupSelected ? selectedPickupPoint.value?.id || "" : null;
    const addressId = !isPickupSelected ? selectedUserAddress.value?.id || "" : null;

    return {
      address_id: addressId,
      delivery_point_id: deliveryPointId,
    };
  });

  // Методы для работы с localStorage
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

  // Загрузка сохраненного состояния при инициализации
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

  // Наблюдатели за изменениями состояния для сохранения в localStorage
  watch(deliveryMethod, (newValue) => {
    saveToLocalStorage(STORAGE_KEY_DELIVERY_METHOD, newValue);
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

  // Загружаем сохраненное состояние при создании store
  loadSavedState();

  // Действия
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
    // Загружаем сохраненное состояние при начале оформления заказа
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

    // Очищаем localStorage
    saveToLocalStorage(STORAGE_KEY_DELIVERY_METHOD, null);
    saveToLocalStorage(STORAGE_KEY_PICKUP_POINT, null);
    saveToLocalStorage(STORAGE_KEY_USER_ADDRESS, null);
    saveToLocalStorage(STORAGE_KEY_PAYMENT_METHOD, null);

    logger.debug("Checkout state reset");
  };

  return {
    // Состояние
    deliveryMethod,
    isCheckoutActive,
    selectedPickupPoint,
    selectedUserAddress,
    paymentMethod,
    isLoading,
    error,

    // Вычисляемые свойства
    canProceed,
    getDeliveryData,

    // Методы
    setDeliveryMethod,
    setPickupPoint,
    setUserAddress,
    setPaymentMethod,
    startCheckout,
    finishCheckout,
    createOrder,
    reset,
    loadSavedState,
  };
});
