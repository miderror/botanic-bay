<script setup lang="ts">
/**
 * Компонент для выбора адреса доставки с возможностью выбора ПВЗ или произвольного адреса
 *
 * Логика выбора:
 * - Если currentMethod === DeliveryMethod.PICKUP:
 *   - На карте отображаются маркеры из visiblePoints (отфильтрованные по видимой области).
 *   - При клике по маркеру вызывается selectPickupPoint, который отправляет uuid на backend.
 * - Если currentMethod === DeliveryMethod.COURIER:
 *   - Отображается выбранный произвольный адрес (или, если ещё не выбран, можно слушать клик по карте).
 *   - При клике по карте (onClick) определяется произвольный адрес, возможно с помощью геокодера.
 *   - Затем этот адрес сохраняется на backend.
 */
import CdekPointIcon from "@/assets/images/cdek-point.svg";
import PointIcon from "@/assets/images/point.svg";
import BaseModal from "@/components/common/BaseModal.vue";
import NotificationToast from "@/components/common/NotificationToast.vue";
import PickupPointModal from "@/components/delivery-section/address/modal/PickupPointModal.vue";
import SearchLocationModal from "@/components/delivery-section/address/modal/SearchLocationModal.vue";
import UserAddressModal from "@/components/delivery-section/address/modal/UserAddressModal.vue";
import { useNotification } from "@/composables/useNotification.ts";
import { cdekService } from "@/services/cdekService.ts";
import {
  type IAddress,
  type IAddressSearchResult,
  type IDeliveryPoint,
  type IDeliveryPointSearchResult,
} from "@/types/cdek.ts";
import { DeliveryMethod, type IUserAddress } from "@/types/order.ts";
import type { LocationData } from "@/types/telegram.ts";
import type { YMap } from "@yandex/ymaps3-types";
import { computed, onMounted, reactive, ref, shallowRef, watch } from "vue";
import {
  YandexMap,
  YandexMapDefaultFeaturesLayer,
  YandexMapDefaultSchemeLayer,
  YandexMapListener,
  YandexMapMarker,
} from "vue-yandex-maps";

const props = defineProps<{
  isOpen: boolean;
  currentMethod: DeliveryMethod | null;
}>();

defineEmits<{
  (e: "close"): void;
}>();

const { message, type, show, showNotification } = useNotification();
const map = shallowRef<null | YMap>(null);

const initialPoint = {
  center: [37.617644, 55.755819], // starting position [lng, lat]
  zoom: 9, // starting zoom
};

const mapBounds = ref<[[number, number], [number, number]] | null>(null);
const allPoints = ref<IDeliveryPoint[]>([]);
const userLocation = ref<LocationData | null>(null);

const selectedMapCustomPoint = ref<[number, number] | null>(null);
const selectedMapPickupPoint = ref<IDeliveryPoint | null>(null);
const selectedAddress = ref<IAddress | null>(null);
const selectedUserAddress = ref<IUserAddress | null>(null);

const isSearchModalOpen = ref<boolean>(false);
const isPickupModalOpen = ref<boolean>(false);
const isUserAddressModalOpen = ref<boolean>(false);

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

// При загрузке компонента получаем список точек с backend
const loadPickupPoints = async () => {
  try {
    const center = map.value?.center;
    if (!center || !Array.isArray(center) || center.length !== 2) {
      console.warn("Некорректный центр карты:", center);
      return;
    }

    // Получаем новые точки от сервиса по текущему центру
    const fetchedPoints = await cdekService.getDeliveryPoints(`${center[0]},${center[1]}`);

    // Проверяем что получен корректный массив
    if (!Array.isArray(fetchedPoints)) {
      console.error("Некорректный ответ от сервиса доставки:", fetchedPoints);
      return;
    }

    // Обновляем allPoints: добавляем только те точки, которых ещё нет в массиве (по уникальному uuid)
    fetchedPoints.forEach((point) => {
      if (point && point.uuid && !allPoints.value.some((existing) => existing.uuid === point.uuid)) {
        allPoints.value.push(point);
      }
    });
  } catch (error) {
    console.error("Ошибка при загрузке ПВЗ:", error);
    showNotification("Произошла ошибка при загрузке ПВЗ", "error");
  }
};

// Вычисляем список точек, попадающих в текущую видимую область карты
const visiblePoints = computed(() => {
  if (!mapBounds.value) {
    // Если границы карты еще не определены, но есть выбранная точка, показываем её
    if (selectedMapPickupPoint.value) {
      return [selectedMapPickupPoint.value];
    }
    return [];
  }

  const [[west, south], [east, north]] = mapBounds.value;

  const filtered = allPoints.value.filter((point) => {
    // Проверяем валидность точки
    if (
      !point ||
      !point.location ||
      typeof point.location.latitude !== "number" ||
      typeof point.location.longitude !== "number" ||
      !isFinite(point.location.latitude) ||
      !isFinite(point.location.longitude)
    ) {
      console.warn("Некорректная точка отфильтрована:", point);
      return false;
    }

    const { latitude, longitude } = point.location;
    const isVisible = latitude >= north && latitude <= south && longitude >= west && longitude <= east;
    return isVisible;
  });

  // Всегда добавляем выбранную точку в видимые, даже если она не попадает в текущие границы
  if (selectedMapPickupPoint.value && !filtered.some((p) => p.uuid === selectedMapPickupPoint.value?.uuid)) {
    filtered.push(selectedMapPickupPoint.value);
  }

  return filtered;
});

// Обработчик клика на карту для выбора произвольного адреса (для DeliveryMethod.COURIER)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const onMapClick = async (object: any, event: any) => {
  try {
    if (props.currentMethod !== DeliveryMethod.COURIER) return;

    const coords = event.coordinates as [number, number];

    // Проверяем валидность координат
    if (
      !coords ||
      !Array.isArray(coords) ||
      coords.length !== 2 ||
      !isFinite(coords[0]) ||
      !isFinite(coords[1])
    ) {
      console.error("Недопустимые координаты:", coords);
      showNotification("Ошибка определения координат", "error");
      return;
    }

    map.value?.setLocation({
      center: coords,
      zoom: 18,
      duration: 300,
    });

    // Получаем адрес с защитой от ошибок
    const address = await cdekService.getAddress(`${coords[0]},${coords[1]}`);

    // Проверяем что адрес получен корректно
    if (!address || typeof address !== "object") {
      console.error("Некорректный адрес получен от сервиса:", address);
      showNotification("Ошибка получения адреса", "error");
      return;
    }

    selectedAddress.value = address;

    // Создаем объект IUserAddress для модального окна
    selectedUserAddress.value = {
      address: address.address,
      latitude: address.latitude,
      longitude: address.longitude,
      apartment: 0, // Значение по умолчанию, будет заполнено пользователем
    };

    selectedMapCustomPoint.value = coords;
    isSearchModalOpen.value = true;
  } catch (error) {
    console.error("Ошибка при обработке клика по карте:", error);
    showNotification("Произошла ошибка при выборе адреса", "error");
  }
};

// Обработчик клика, когда пользователь выбирает ПВЗ/постамат
const selectPickupPoint = (point: IDeliveryPoint) => {
  selectedMapPickupPoint.value = point;

  map.value?.setLocation({
    center: [point.location.longitude, point.location.latitude],
    zoom: 18,
    duration: 300,
  });

  // Принудительно обновляем границы карты после завершения анимации
  setTimeout(() => {
    updateMapBounds();
  }, 350); // Немного больше чем duration анимации

  isPickupModalOpen.value = true;
};

// Функция для обновления границ карты
const updateMapBounds = () => {
  if (map.value && map.value.bounds) {
    mapBounds.value = [
      [map.value.bounds[0][0], map.value.bounds[0][1]],
      [map.value.bounds[1][0], map.value.bounds[1][1]],
    ];
    if (props.currentMethod === DeliveryMethod.PICKUP) loadPickupPoints();
  }
};

// Настройки для компонента YandexMapListener — подписка на события карты
const listenerSettings = reactive({
  // Событие начала действия (например, перетаскивания карты)
  onActionStart: () => {
    console.log("Действие начато. Текущие границы карты:", map.value?.bounds);
  },
  // Событие окончания действия — обновляем mapBounds для пересчёта visiblePoints
  onActionEnd: () => {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    debounceTimer = setTimeout(updateMapBounds, 500);
  },
  // Событие клика по карте
  onClick: onMapClick,
});

const handlePickupModalClose = () => {
  isPickupModalOpen.value = false;
};

const handleUserAddressModalClose = () => {
  isUserAddressModalOpen.value = false;
};

const showUserAddressModal = () => {
  isUserAddressModalOpen.value = true;
  isSearchModalOpen.value = false;
};

// Обработчик выбора результата из поиска
const handleSelectResult = async (result: IAddressSearchResult | IDeliveryPointSearchResult) => {
  try {
    if (props.currentMethod === DeliveryMethod.PICKUP) {
      // Для режима самовывоза - ищем точку ПВЗ по координатам
      const deliveryResult = result as IDeliveryPointSearchResult;

      // Ищем точку в уже загруженных точках по координатам
      let point = allPoints.value.find(
        (p) =>
          Math.abs(p.location.latitude - deliveryResult.latitude) < 0.001 &&
          Math.abs(p.location.longitude - deliveryResult.longitude) < 0.001,
      );

      // Если точка не найдена в загруженных, получаем её отдельно
      if (!point) {
        const fetchedPoints = await cdekService.getDeliveryPoints(
          `${deliveryResult.longitude},${deliveryResult.latitude}`,
        );
        point = fetchedPoints.find(
          (p) =>
            Math.abs(p.location.latitude - deliveryResult.latitude) < 0.001 &&
            Math.abs(p.location.longitude - deliveryResult.longitude) < 0.001,
        );

        if (point) {
          // Добавляем новую точку в список
          allPoints.value.push(point);
        }
      }

      if (point) {
        selectPickupPoint(point);
      } else {
        console.error(
          "Не удалось найти ПВЗ по координатам:",
          deliveryResult.latitude,
          deliveryResult.longitude,
        );
        showNotification("Ошибка при выборе ПВЗ", "error");
      }
    } else if (props.currentMethod === DeliveryMethod.COURIER) {
      // Для режима доставки - устанавливаем выбранный адрес
      const addressResult = result as IAddressSearchResult;

      // Создаем объект IAddress из результата поиска
      selectedAddress.value = {
        address: addressResult.full_address || addressResult.title,
        latitude: addressResult.latitude,
        longitude: addressResult.longitude,
      };

      // Создаем объект IUserAddress для модального окна
      selectedUserAddress.value = {
        address: addressResult.full_address || addressResult.title,
        latitude: addressResult.latitude,
        longitude: addressResult.longitude,
        apartment: 0, // Значение по умолчанию, будет заполнено пользователем
      };

      // Устанавливаем маркер на карте
      selectedMapCustomPoint.value = [addressResult.longitude, addressResult.latitude];

      // Перемещаем карту к выбранному адресу
      map.value?.setLocation({
        center: [addressResult.longitude, addressResult.latitude],
        zoom: 18,
        duration: 300,
      });

      // Открываем модальное окно для ввода квартиры
      showUserAddressModal();
    }
  } catch (error) {
    console.error("Ошибка при обработке выбранного результата:", error);
    showNotification("Произошла ошибка при выборе адреса", "error");
  }
};

watch(
  () => props.isOpen,
  (newValue) => {
    isSearchModalOpen.value = newValue;
  },
);

watch(isPickupModalOpen, (newValue) => {
  isSearchModalOpen.value = !newValue;
});

watch(isSearchModalOpen, (newValue) => {
  if (newValue) isUserAddressModalOpen.value = false;
});

onMounted(() => {
  if (!window.Telegram?.WebApp) return;
  const webApp = window.Telegram?.WebApp;
  const locationManager = webApp.LocationManager;

  watch(
    map,
    (newMap) => {
      if (newMap) {
        locationManager.init(() => {
          locationManager.getLocation(onLocationRequest);
        });

        // Инициализируем границы карты при первой загрузке
        setTimeout(() => {
          updateMapBounds();
        }, 1000); // Даем время карте полностью загрузиться

        if (props.currentMethod === DeliveryMethod.PICKUP) {
          loadPickupPoints();
        }
      }
    },
    { immediate: true },
  );
});

// Вызывается при инициализации компонента, когда Telegram WebApp LocationManager
// получает разрешение на доступ к геолокации
const onLocationRequest = (location?: LocationData | null) => {
  if (!location) return;

  userLocation.value = location;
  map.value?.setLocation({
    center: [location.longitude, location.latitude],
    zoom: 15,
  });
};
</script>

<template>
  <BaseModal
    :modelValue="isOpen"
    @update:modelValue="$emit('close')"
    fullscreen
  >
    <NotificationToast
      :show="show"
      :message="message"
      :type="type"
      class="location-selector-notification"
    />
    <SearchLocationModal
      :deliveryMethod="props.currentMethod || DeliveryMethod.PICKUP"
      :userLocation="userLocation"
      :isOpen="isSearchModalOpen"
      :showButton="Boolean(selectedAddress)"
      @buttonClick="showUserAddressModal"
      @selectResult="handleSelectResult"
    />

    <PickupPointModal
      :isOpen="isPickupModalOpen"
      :point="selectedMapPickupPoint"
      @close="handlePickupModalClose"
      @closeParentModal="$emit('close')"
    />
    <UserAddressModal
      v-if="selectedUserAddress"
      :address="selectedUserAddress"
      :isOpen="isUserAddressModalOpen"
      @close="handleUserAddressModalClose"
      @closeParentModal="$emit('close')"
    />

    <yandex-map
      v-model="map"
      :settings="{
        location: {
          ...initialPoint,
          duration: 2500,
        },
        behaviors: ['drag', 'scrollZoom', 'pinchZoom', 'magnifier', 'dblClick'],
      }"
      width="100%"
      height="100%"
    >
      <!-- Основной слой карты -->
      <yandex-map-default-scheme-layer />
      <yandex-map-default-features-layer />

      <!-- Слушатель событий карты -->
      <yandex-map-listener :settings="listenerSettings" />

      <!-- Отрисовка маркеров для ПВЗ/постаматов -->
      <div v-if="currentMethod === DeliveryMethod.PICKUP">
        <yandex-map-marker
          v-for="(point, index) in visiblePoints"
          :key="point.uuid || index"
          :settings="{
            coordinates: [point.location.longitude, point.location.latitude],
            onClick: () => selectPickupPoint(point),
          }"
          position="top left-center"
        >
          <img
            :src="CdekPointIcon"
            class="marker"
            alt="V"
          />
        </yandex-map-marker>
      </div>

      <!-- Если выбран произвольный адрес, можно отобразить маркер -->
      <div v-if="currentMethod === DeliveryMethod.COURIER">
        <yandex-map-marker
          v-if="
            selectedMapCustomPoint &&
            Array.isArray(selectedMapCustomPoint) &&
            selectedMapCustomPoint.length === 2
          "
          :settings="{ coordinates: selectedMapCustomPoint }"
          position="top left-center"
        >
          <img
            :src="PointIcon"
            class="marker"
            alt="V"
          />
        </yandex-map-marker>
      </div>
    </yandex-map>
  </BaseModal>
</template>

<style scoped>
.marker {
  width: 36px !important;
  height: 36px !important;
  min-width: 36px !important;
  min-height: 36px !important;
  transition: transform 0.2s ease;
  cursor: pointer;
  z-index: 1000;
  position: relative;
  display: block;
  object-fit: contain;
}

.marker:active,
.marker:hover {
  transform: scale(1.2);
}

.location-selector-notification {
  left: 50%;
  transform: translateX(-50%);
  margin: 0;
  bottom: unset;
  top: 46px;
  z-index: 2000;
}
</style>
