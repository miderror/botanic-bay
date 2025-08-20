export function useFormatDate() {
  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
    });
  };

  const formatDeliveryDate = (order: { planned_shipping_date: string | null; created_at: string }) => {
    if (!order.planned_shipping_date) {
      return formatDate(order.created_at);
    }
    return formatDate(order.planned_shipping_date);
  };

  return {
    formatDate,
    formatDeliveryDate,
  };
}
