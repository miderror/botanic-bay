/**
 * Стор для управления адресами доставки и пунктами выдачи
 * Используется для получения, сохранения и удаления адресов и пунктов выдачи
 * в приложении.
 */
import { orderService } from "@/services/orderService.ts";
import type { IDeliveryPoint } from "@/types/cdek.ts";
import type { IUserAddress, IUserDeliveryPoint } from "@/types/order.ts";
import { defineStore } from "pinia";
import { ref } from "vue";

export const useDeliveryPreferences = defineStore("deliveryPreferences", () => {
  const addresses = ref<IUserAddress[]>([]);
  const deliveryPoints = ref<IUserDeliveryPoint[]>([]);
  const error = ref<string | null>(null);

  const fetchAddresses = async () => {
    const response = await orderService.getAddresses();
    if (!response) return;
    addresses.value = response;
  };

  const fetchDeliveryPoints = async () => {
    const response = await orderService.getDeliveryPoints();
    if (!response) return;
    deliveryPoints.value = response;
  };

  const saveAddress = async (data: IUserAddress) => {
    const response = await orderService.saveAddress(data);
    addresses.value.push(response);
  };

  const updateAddress = async (addressId: string, data: IUserAddress) => {
    const response = await orderService.updateAddress(addressId, data);
    // Обновляем адрес в массиве вместо добавления нового
    const index = addresses.value.findIndex((addr) => addr.id === addressId);
    if (index !== -1) {
      addresses.value[index] = response;
    }
  };

  const deleteAddress = async (data: IUserAddress) => {
    if (!data.id) return;
    await orderService.deleteAddress(data.id);
    addresses.value = addresses.value.filter((item) => item.id !== data.id);
  };

  const saveDeliveryPoint = async (data: IDeliveryPoint) => {
    const response = await orderService.saveDeliveryPoint(data);
    deliveryPoints.value.push(response);
  };

  const deleteDeliveryPoint = async (data: IUserDeliveryPoint) => {
    await orderService.deleteDeliveryPoint(data.id);
    deliveryPoints.value = deliveryPoints.value.filter((item) => item.id !== data.id);
  };

  return {
    addresses,
    deliveryPoints,
    error,
    fetchAddresses,
    fetchDeliveryPoints,
    saveAddress,
    updateAddress,
    saveDeliveryPoint,
    deleteAddress,
    deleteDeliveryPoint,
  };
});
