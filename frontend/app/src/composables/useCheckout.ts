import { useNotification } from "@/composables/useNotification";
import { usePayment } from "@/composables/usePayment";
import { PAYMENT_PROVIDERS } from "@/constants/payment";
import { useCartStore } from "@/stores/cart";
import { useCheckoutStore } from "@/stores/checkout";
import type { ICreateOrder, IUserAddress, IUserDeliveryPoint } from "@/types/order";
import { DeliveryMethod, PaymentMethod } from "@/types/order";
import { logger } from "@/utils/logger";
import { storeToRefs } from "pinia";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

export function useCheckout() {
  // Инициализация сторов и служб
  const router = useRouter();
  const checkoutStore = useCheckoutStore();
  const cartStore = useCartStore();
  const { showNotification } = useNotification();
  const { initiateWidgetPayment } = usePayment();
  const { promoCode } = storeToRefs(checkoutStore);
  const { deliveryCost } = storeToRefs(checkoutStore);

  // Получаем реактивные ссылки на состояния из сторов
  const {
    isCheckoutActive,
    deliveryMethod: currentDeliveryMethod,
    selectedPickupPoint,
    selectedUserAddress,
    paymentMethod: selectedPaymentMethod,
    isLoading,
    error,
  } = storeToRefs(checkoutStore);

  // Загружаем сохраненное состояние
  checkoutStore.loadSavedState();

  const { cart } = storeToRefs(cartStore);

  // Состояние для оверлея загрузки платежного виджета
  const isPaymentProcessing = ref(false);

  // Вычисляемые свойства
  const canPay = computed(() => checkoutStore.canProceed);

  const totalAmount = computed(() => {
    const cartTotal = cart.value?.total || 0;
    const delivery = deliveryCost.value || 0;
    
    const personalDiscountMultiplier = (100 - (checkoutStore.userDiscountPercent || 0)) / 100;
    const totalAfterPersonalDiscount = cartTotal * personalDiscountMultiplier;

    const promoDiscountAmount = (cartTotal * (checkoutStore.discountPercent || 0)) / 100;
    const finalTotal = totalAfterPersonalDiscount - promoDiscountAmount + delivery;

    return Math.max(0, finalTotal);
  });

  const getDeliveryData = computed(() => {
    const isPickupSelected = currentDeliveryMethod.value === DeliveryMethod.PICKUP;

    const deliveryPointId = isPickupSelected ? selectedPickupPoint.value?.id || "" : null;
    const addressId = !isPickupSelected ? selectedUserAddress.value?.id || "" : null;

    return {
      address_id: addressId,
      delivery_point_id: deliveryPointId,
    };
  });

  // Методы управления состоянием checkout
  const startCheckout = () => {
    checkoutStore.startCheckout();
    logger.debug("Checkout mode started");
  };

  const finishCheckout = () => {
    checkoutStore.finishCheckout();
    logger.debug("Checkout mode finished");
  };

  const reset = () => {
    checkoutStore.reset();
    logger.debug("Checkout state reset");
  };

  // Методы для работы с адресом доставки
  const setDeliveryMethod = (method: DeliveryMethod) => {
    checkoutStore.setDeliveryMethod(method);
    logger.debug("Delivery method changed", { method });
  };

  const setPickupPoint = (point: IUserDeliveryPoint) => {
    checkoutStore.setPickupPoint(point);
    logger.debug("Pickup point selected", { pointId: point.id });
  };

  const setUserAddress = (address: IUserAddress) => {
    checkoutStore.setUserAddress(address);
    logger.debug("User address selected", { addressId: address.id });
  };

  // Методы для работы с оплатой
  const setPaymentMethod = (method: PaymentMethod) => {
    checkoutStore.setPaymentMethod(method);
    logger.debug("Payment method set", { method });
  };

  // Методы для создания заказа
  const getCheckoutData = (): ICreateOrder | null => {
    if (!currentDeliveryMethod.value || !selectedPaymentMethod.value) {
      logger.debug("Cannot get checkout data - missing required fields");
      return null;
    }

    const orderData: ICreateOrder = {
      delivery_method: currentDeliveryMethod.value,
      payment_method: selectedPaymentMethod.value,
      address_id: getDeliveryData.value.address_id || undefined,
      delivery_point_id: getDeliveryData.value.delivery_point_id || undefined,
      promo_code: checkoutStore.promoCode || undefined,
    };

    logger.debug("Checkout data prepared", { orderData });
    return orderData;
  };


  const createOrder = async (orderData: ICreateOrder) => {
    try {
      logger.info("Creating order", { orderData });
      const response = await checkoutStore.createOrder(orderData);
      logger.info("Order created successfully", { orderId: response.id });
      return response;
    } catch (err) {
      logger.error("Failed to create order", { error: err });
      throw err;
    }
  };

  // Обновленный метод для обработки создания заказа и оплаты
  const processPayment = async () => {
    try {
      if (!canPay.value) {
        showNotification("Невозможно создать заказ: проверьте данные", "error");
        return false;
      }

      const orderData = getCheckoutData();

      if (!orderData) {
        showNotification("Заполните все необходимые данные", "error");
        return false;
      }

      // Активируем оверлей загрузки
      isPaymentProcessing.value = true;

      // Проверяем активность корзины перед созданием заказа
      try {
        await cartStore.fetchCart();

        // Если корзина пуста или неактивна - сообщаем об ошибке
        if (!cart.value || !cart.value.is_active || cart.value.items.length === 0) {
          showNotification("Корзина пуста или неактивна. Пожалуйста, добавьте товары в корзину", "error");
          isPaymentProcessing.value = false;
          return false;
        }
      } catch (cartError) {
        logger.error("Failed to check cart before order creation", { error: cartError });
      }

      logger.info("Processing payment and creating order", { orderData });


      logger.info("Processing payment and creating order", { orderData });

      // Создаем заказ
      const order = await createOrder(orderData);
      logger.info("Order created successfully, initializing payment", { orderId: order.id });

      // Инициируем платеж через виджет ЮКассы
      const paymentCreated = await initiateWidgetPayment(order.id, PAYMENT_PROVIDERS.YOOKASSA);

      // Деактивируем оверлей загрузки после получения ответа
      if (!paymentCreated) {
        isPaymentProcessing.value = false;
        logger.error("Failed to create payment after order creation", {
          orderId: order.id,
        });
        showNotification("Заказ создан, но возникла ошибка при создании платежа", "error");

        // Если платеж не удалось создать, перенаправляем на страницу заказов
        await router.push({ name: "profile-orders" });
        return false;
      }

      return true;
    } catch (error) {
      // Деактивируем оверлей загрузки в случае ошибки
      isPaymentProcessing.value = false;

      // Обработка конкретной ошибки "Active cart not found"
      if (error instanceof Error && error.message.includes("Active cart not found")) {
        showNotification("Корзина не найдена. Пожалуйста, добавьте товары в корзину", "error");
        // Пробуем восстановить корзину
        try {
          await cartStore.fetchCart();
        } catch (cartError) {
          logger.error("Failed to refresh cart after error", { error: cartError });
        }
      } else {
        showNotification("Не удалось создать заказ", "error");
      }

      logger.error("Failed to process payment and create order", { error });
      return false;
    }
  };

  // Возвращаем публичное API композабла
  return {
    // Состояния
    isCheckoutActive,
    currentDeliveryMethod,
    selectedPickupPoint,
    selectedUserAddress,
    selectedPaymentMethod,
    isLoading,
    error,
    canPay,
    totalAmount,
    deliveryCost,
    isPaymentProcessing,

    // Вычисляемые свойства
    getDeliveryData: getDeliveryData,

    // Методы управления состоянием
    startCheckout,
    finishCheckout,
    reset,

    // Методы работы с адресом
    setDeliveryMethod,
    setPickupPoint,
    setUserAddress,

    // Методы работы с оплатой
    setPaymentMethod,

    // Методы создания заказа
    getCheckoutData,
    createOrder,

    // Обновленный метод для обработки платежа
    processPayment,
  };
}
