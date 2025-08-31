import { logger } from "@/utils/logger";

export function useImageUrl() {
  const getImageUrl = (relativePath: string | null): string => {
    const placeholder = "/images/placeholder.jpg";
    if (!relativePath) {
      return placeholder;
    }

    if (relativePath.startsWith("http")) {
      return relativePath;
    }

    if (relativePath.includes("/backend/media/")) {
      relativePath = relativePath.split("/backend/media/").pop() || '';
    }

    if (relativePath.includes("/media/")) {
        return `/${relativePath.replace(/^\/+/, '')}`;
    }

    const cleanedPath = relativePath.replace(/^\/+/, '');
    
    const finalUrl = `/media/${cleanedPath}`;
    
    return finalUrl;
  };

  const handleImageError = (e: Event) => {
    const img = e.target as HTMLImageElement;
    if (img.src.includes("placeholder.jpg")) return;
    img.src = "/images/placeholder.jpg";
    logger.warn("Failed to load image, using placeholder", { originalSrc: img.src });
  };

  return {
    getImageUrl,
    handleImageError,
  };
}