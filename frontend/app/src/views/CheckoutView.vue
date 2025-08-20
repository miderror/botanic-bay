<script setup lang="ts">
import AddressModal from "@/components/delivery-section/address/modal/AddressModal.vue";
import LocationIcon from "@/components/icons/LocationIcon.vue";
import { useCart } from "@/composables/useCart";
import { orderService } from "@/services/orderService";
import { useCheckoutStore } from "@/stores/checkout";
import type { IPaymentMethod, IUserAddress, IUserDeliveryPoint } from "@/types/order";
import { DeliveryMethod } from "@/types/order";
import { logger } from "@/utils/logger";
import { computed, onMounted, ref } from "vue";

const { cart } = useCart();
const checkoutStore = useCheckoutStore();

const showAddressModal = ref(false);
const paymentMethods = ref<IPaymentMethod[]>([]);
const isLoading = ref(false);

// Получаем значения из store
const currentDeliveryMethod = computed(() => checkoutStore.deliveryMethod);
const selectedPaymentMethod = computed(() => checkoutStore.paymentMethod);

// Вычисляемые свойства для адреса
const currentAddress = computed(() => {
  return currentDeliveryMethod.value === DeliveryMethod.PICKUP
    ? checkoutStore.selectedPickupPoint
    : { address: checkoutStore.deliveryAddress };
});

const displayAddress = computed(() => {
  if (currentDeliveryMethod.value === DeliveryMethod.PICKUP) {
    const point = checkoutStore.selectedPickupPoint;
    return point ? `${point.name}, ${point.address}` : "Укажите адрес доставки";
  }
  return checkoutStore.deliveryAddress || "Укажите адрес доставки";
});

const hasAddress = computed(() => {
  return currentDeliveryMethod.value === DeliveryMethod.PICKUP
    ? !!checkoutStore.selectedPickupPoint
    : !!checkoutStore.deliveryAddress;
});

// Методы
const setDeliveryMethod = (method: DeliveryMethod) => {
  checkoutStore.setDeliveryMethod(method);
};

const selectPaymentMethod = (method: IPaymentMethod) => {
  if (!method.is_available) return;
  checkoutStore.setPaymentMethod(method.id);
};

const handleAddressAction = () => {
  showAddressModal.value = true;
};

const handleAddressSelect = (method: DeliveryMethod, address: IUserDeliveryPoint | IUserAddress) => {
  checkoutStore.setDeliveryMethod(method);

  if (method === DeliveryMethod.PICKUP) {
    checkoutStore.setPickupPoint(address as IUserDeliveryPoint);
  } else {
    checkoutStore.setDeliveryAddress(address.address);
  }

  showAddressModal.value = false;
};

// Инициализация
onMounted(async () => {
  try {
    isLoading.value = true;
    const methods = await orderService.getPaymentMethods();
    paymentMethods.value = methods;
  } catch (error) {
    logger.error("Failed to initialize checkout", { error });
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div class="checkout-view">
    <div class="checkout-content">
      <h1 class="checkout-title">Оформление заказа</h1>

      <!-- Секция способа доставки -->
      <div class="section">
        <h2 class="section-title">Способ доставки</h2>

        <div class="delivery-section">
          <!-- Переключатель способа доставки -->
          <div class="delivery-toggle">
            <button
              class="toggle-btn left"
              :class="{ active: currentDeliveryMethod === DeliveryMethod.PICKUP }"
              @click="setDeliveryMethod(DeliveryMethod.PICKUP)"
            >
              САМОВЫВОЗ
            </button>
            <button
              class="toggle-btn right"
              :class="{ active: currentDeliveryMethod === DeliveryMethod.COURIER }"
              @click="setDeliveryMethod(DeliveryMethod.COURIER)"
            >
              КУРЬЕР
            </button>
          </div>

          <!-- Блок адреса -->
          <div class="address-block">
            <div class="address-content">
              <LocationIcon class="location-icon" />
              <span class="address-text">
                {{ displayAddress }}
              </span>
            </div>
          </div>

          <div class="address-action">
            <button
              class="action-button"
              @click="handleAddressAction"
            >
              {{ hasAddress ? "ИЗМЕНИТЬ АДРЕС" : "ДОБАВИТЬ АДРЕС +" }}
            </button>
          </div>
        </div>

        <div class="delivery-info">Доставка в пункт выдачи, бесплатно</div>
      </div>

      <!-- Список товаров -->
      <div class="order-items">
        <div
          v-for="(item, index) in cart?.items"
          :key="item.id"
          class="order-item"
          :class="{
            'first-item': index === 0,
            'last-item': index === cart.items.length - 1,
          }"
        >
          <img
            :src="item.image_url"
            :alt="item.product_name"
            class="item-image"
          />
          <span class="quantity">{{ item.quantity }} шт.</span>
          <span class="delivery-date">Завтра</span>
        </div>
      </div>

      <!-- Способ оплаты -->
      <div class="section">
        <h2 class="section-title">Способ оплаты</h2>
        <div class="payment-section">
          <div class="payment-methods">
            <button
              v-for="method in paymentMethods"
              :key="method.id"
              class="payment-method"
              :class="{
                active: selectedPaymentMethod === method.id,
                disabled: !method.is_available,
              }"
              @click="selectPaymentMethod(method)"
            >
              <img
                :src="method.icon"
                :alt="method.name"
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <AddressModal
    v-if="showAddressModal"
    :initial-method="currentDeliveryMethod"
    :initial-address="currentAddress"
    @close="showAddressModal = false"
    @save="handleAddressSelect"
  />
</template>

<style scoped>
.checkout-view {
  min-height: 100vh;
  padding-bottom: 60px;
  background: #fff;
}

.checkout-content {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.checkout-title {
  font-size: 24px;
  font-weight: 600;
  color: #252525;
  margin-bottom: 30px;
}

.section {
  margin-bottom: 40px;
}

.section-title,
.delivery-info {
  font-size: 18px;
  font-weight: 500;
  color: #252525;
  margin-bottom: 20px;
}

.delivery-section {
  background: #f8f8f8;
  border-radius: 16px;
  padding: 25px;
}

.delivery-info {
  margin-top: 20px;
  margin-bottom: 0px;
}

.delivery-toggle {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  gap: 5px; /* Добавляем небольшой промежуток между кнопками */
}

.toggle-btn {
  width: 160px; /* Фиксированная одинаковая ширина */
  padding: 12px 0;
  border: none;
  font-weight: 700;
  font-size: 10px; /* Уменьшаем размер шрифта */
  letter-spacing: 0.5px; /* Добавляем небольшой трекинг */
  cursor: pointer;
  transition: all 0.2s;
  background: #252525;
  color: white;
  text-transform: uppercase;
}

.toggle-btn.left {
  border-top-left-radius: 50px;
  border-bottom-left-radius: 50px;
}

.toggle-btn.right {
  border-top-right-radius: 50px;
  border-bottom-right-radius: 50px;
}

.toggle-btn.active {
  background: #ffb43d;
}

.address-block {
  border-radius: 8px;
  padding: 16px;
  /* margin-bottom: 12px; */
}

.address-content {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px; /* Добавляем отступ до кнопки */
}

.location-icon {
  font-size: 20px;
}

.address-text {
  color: #666;
  font-size: 16px;
  font-weight: 600;
}

/* Контейнер для кнопки добавления/изменения адреса */
.address-action {
  display: flex;
  justify-content: center; /* Центрируем содержимое */
  /* margin-top: 20px; */
}

/* Стили для кнопки добавления адреса */
.action-button {
  width: fit-content;
  padding: 14px 32px;
  border: none;
  border-radius: 50px;
  background: #252525;
  color: white;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
}

.order-items {
  background: transparent; /* Убираем фон у внешней подложки */
  border-radius: 16px;
  padding: 0; /* Убираем padding */
  margin-bottom: 40px;
  display: flex;
  flex-direction: column;
  gap: 3px; /* Прозрачный гэп между элементами */
}

.order-item {
  display: grid;
  grid-template-columns: auto 1fr auto; /* три колонки: изображение, пространство для центрирования, срок */
  align-items: center;
  padding: 16px;
  background: #f8f8f8;
}

.first-item {
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}

.last-item {
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 16px;
}

.order-item:last-child {
  margin-bottom: 0; /* Убираем отступ у последнего элемента */
}

.item-image {
  width: 100px;
  height: 100px;
  object-fit: contain;
  border-radius: 8px;
}

.item-details {
  display: flex;
  gap: 24px; /* Увеличиваем расстояние между элементами */
  color: #666;
  align-items: center;
}

.quantity {
  grid-column: 2; /* Помещаем в центральную колонку */
  text-align: center; /* Центрируем текст */
  color: #666;
  font-size: 14px;
}

.payment-section {
  background: #f8f8f8;
  border-radius: 16px;
  padding: 20px;
}

.payment-methods {
  display: flex;
  justify-content: center; /* Центрируем методы оплаты */
  gap: 12px;
  margin-bottom: 20px;
}

.payment-method {
  padding: 16px 24px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.payment-method.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.payment-method.active {
  border-color: #ffb43d;
}

.payment-method img {
  height: 24px;
}

.bottom-panel {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  padding: 12px 20px;
  background: #252525;
  gap: 16px;
}

.close-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
}

.pay-btn {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 50px;
  background: #66ca1a;
  color: white;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.pay-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.delivery-date {
  grid-column: 3; /* Помещаем в правую колонку */
  color: #252525;
  font-size: 16px;
  font-weight: 700;
}

@media (max-width: 480px) {
  .checkout-content {
    padding: 16px;
  }

  .delivery-section,
  .payment-section,
  .order-items {
    padding: 16px;
  }

  .toggle-btn {
    padding: 12px 0;
    font-size: 13px;
  }

  .payment-method {
    padding: 12px 16px;
  }

  .bottom-panel {
    padding: 8px 16px;
  }
}
</style>
