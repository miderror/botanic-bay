import type { IOrder } from "@/types/order";

export function useOrderFormatting() {
  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
    });
  };

  const formatDeliveryDate = (order: IOrder) => {
    if (!order.planned_shipping_date) {
      return formatDate(order.created_at);
    }
    return formatDate(order.planned_shipping_date);
  };

  const formatStatus = (status: string) => {
    const statuses: Record<string, string> = {
      pending: "Ожидает оплаты",
      paid: "Оплачен",
      processing: "В обработке",
      shipped: "Отправлен",
      delivered: "Доставлен",
      cancelled: "Отменён",
    };
    return statuses[status] || status;
  };

  const getStatusClass = (status: string) => {
    return `status-${status}`;
  };

  const formatDeliveryMethod = (method: string) => {
    const methods: Record<string, string> = {
      courier: "Курьерская доставка",
      pickup: "Самовывоз",
    };
    return methods[method] || method;
  };

  const canBeCancelled = (status: string) => {
    return ["pending", "processing"].includes(status);
  };

  return {
    formatDate,
    formatDeliveryDate,
    formatStatus,
    getStatusClass,
    formatDeliveryMethod,
    canBeCancelled,
  };
}
