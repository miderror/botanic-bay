export const formatPrice = (price: number): string => {
  // Округляем до целого числа в большую сторону
  const roundedPrice = Math.ceil(price);

  // Форматируем число с разделителями тысяч
  const formattedPrice = roundedPrice.toLocaleString("ru-RU");

  return `${formattedPrice} р`;
};
