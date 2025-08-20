import { logger } from "@/utils/logger";

export function useImageUrl() {
  const getImageUrl = (url: string | null) => {
    if (!url) return "/images/placeholder.jpg";

    // Если это полный URL или начинается с /media
    if (url.startsWith("http") || url.startsWith("/media")) {
      return url;
    }

    // Иначе добавляем префикс
    return `/media/products/${url}`;
  };

  const handleImageError = (e: Event) => {
    const img = e.target as HTMLImageElement;
    img.src = "/images/placeholder.jpg";
    logger.warn("Failed to load image, using placeholder");
  };

  return {
    getImageUrl,
    handleImageError,
  };
}
