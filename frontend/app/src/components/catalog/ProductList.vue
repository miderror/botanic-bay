<script setup lang="ts">
/**
 * Компонент для отображения списка товаров в каталоге
 * Включает фильтры, поиск и подгрузку товаров при скролле
 */
import "@/assets/styles/catalog.css";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import { useSearch } from "@/composables/useSearch";
import { useViewport } from "@/composables/useViewport";
import { CATALOG_PRODUCTS_PER_PAGE } from "@/config/pagination";
import { productService } from "@/services/productService";
import type { IProduct } from "@/types/product";
import { logger } from "@/utils/logger";
import { debounce } from "lodash-es";
import { nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import CategoryMenu from "./CategoryMenu.vue";
import ProductCard from "./ProductCard.vue";
import SearchBar from "./SearchBar.vue";

const { isSearchActive, searchProducts, setSearchActive, resetSearch } = useSearch();

// Состояние компонента
const products = ref<IProduct[]>([]);
const initialLoading = ref(true);
const loadingMore = ref(false);
const error = ref<string | null>(null);
const currentPage = ref(1);
const hasMore = ref(true);
const isAllLoaded = ref(false);
const selectedCategory = ref("");
const categories = ref<string[]>([]);
const searchQuery = ref("");
// const isSearchActive = ref(false)
const isScrolling = ref(false);
const lastScrollPosition = ref(0);

// Refs для DOM элементов
const productsContainer = ref<HTMLElement | null>(null);
const searchBarRef = ref<InstanceType<typeof SearchBar> | null>(null);

// Композаблы
const { isKeyboardVisible } = useViewport();

// Добавим загрузку всех категорий отдельно
const loadCategories = async () => {
  try {
    logger.debug("Loading all categories");
    const allCategories = await productService.getCategories();
    categories.value = allCategories;
    logger.debug("All categories loaded", {
      categories: categories.value,
      count: categories.value.length,
    });
  } catch (error) {
    logger.error("Failed to load categories", { error });
  }
};

// Загрузка продуктов
const loadProducts = async (loadMore: boolean = false) => {
  try {
    // Если это не подгрузка следующей страницы - сбрасываем состояние
    if (!loadMore) {
      products.value = [];
      currentPage.value = 1;
      hasMore.value = true;
      isAllLoaded.value = false;
    }

    // Проверяем возможность загрузки
    if (isAllLoaded.value || !hasMore.value || loadingMore.value) {
      logger.debug("Skipping load", {
        isAllLoaded: isAllLoaded.value,
        hasMore: hasMore.value,
        loadingMore: loadingMore.value,
        currentPage: currentPage.value,
      });
      return;
    }

    // Устанавливаем соответствующий флаг загрузки
    if (loadMore) {
      loadingMore.value = true;
      // Увеличиваем страницу ДО загрузки при подгрузке следующей порции
      currentPage.value++;
    } else {
      initialLoading.value = true;
    }

    error.value = null;

    logger.debug("Loading products", {
      page: currentPage.value,
      perPage: CATALOG_PRODUCTS_PER_PAGE,
      category: selectedCategory.value || "all",
      loadMore,
    });

    // Запрашиваем данные с сервера
    const response = await productService.getProducts(
      currentPage.value,
      CATALOG_PRODUCTS_PER_PAGE,
      selectedCategory.value || undefined,
    );

    logger.debug("API response received", {
      itemsReceived: response.items.length,
      totalItems: response.total,
      hasMore: response.items.length > 0,
      currentTotal: products.value.length,
      currentPage: currentPage.value,
    });

    // Обрабатываем полученные данные
    if (loadMore) {
      products.value = [...products.value, ...response.items];
    } else {
      products.value = response.items;
    }

    // Проверяем наличие следующих страниц
    hasMore.value = products.value.length < response.total;

    // Проверяем завершение загрузки всех товаров
    if (response.items.length === 0 || products.value.length >= response.total) {
      isAllLoaded.value = true;
      hasMore.value = false;
      logger.info("All products loaded", {
        totalLoaded: products.value.length,
        totalAvailable: response.total,
        remainingItems: response.total - products.value.length,
        currentPage: currentPage.value,
      });
    } else {
      logger.debug("More products available", {
        currentlyLoaded: products.value.length,
        totalAvailable: response.total,
        remainingItems: response.total - products.value.length,
        currentPage: currentPage.value,
      });
    }
  } catch (err) {
    // При ошибке откатываем изменение страницы
    if (loadMore) {
      currentPage.value--;
    }
    error.value = err instanceof Error ? err.message : "Failed to load products";
    logger.error("Product loading failed", {
      error: err,
      page: currentPage.value,
      loadMore,
    });
    throw err;
  } finally {
    if (loadMore) {
      loadingMore.value = false;
      logger.debug("Load more completed", {
        currentPage: currentPage.value,
        totalItems: products.value.length,
        hasMore: hasMore.value,
      });
    } else {
      initialLoading.value = false;
      logger.debug("Initial load completed", {
        itemsLoaded: products.value.length,
        hasMore: hasMore.value,
      });
    }
  }
};

// Улучшенный обработчик скролла
const handleScroll = async () => {
  if (
    !productsContainer.value ||
    isAllLoaded.value ||
    loadingMore.value ||
    isScrolling.value ||
    isSearchActive.value
  ) {
    return;
  }

  const container = productsContainer.value;
  const scrollOffset = container.scrollTop + container.clientHeight;
  const triggerThreshold = container.scrollHeight - container.clientHeight * 1.5;

  // Проверяем, нужна ли подгрузка:
  // 1. Если есть скролл и достигли порога
  // 2. Если скролла нет, но контейнер не заполнен
  const needsMoreContent =
    scrollOffset >= triggerThreshold || // условие для скролла
    (!hasVerticalScrollbar(container) && hasMore.value); // условие для большого экрана

  if (needsMoreContent) {
    try {
      const previousHeight = container.scrollHeight;
      await loadProducts(true);

      const heightDiff = container.scrollHeight - previousHeight;
      if (heightDiff > 0 && isKeyboardVisible.value) {
        container.scrollTop -= heightDiff / 2;
      }
    } catch (err) {
      logger.error("Error loading more products", { error: err });
    }
  }
};

// Вспомогательная функция для проверки наличия вертикального скролла
const hasVerticalScrollbar = (element: HTMLElement): boolean => {
  return element.scrollHeight > element.clientHeight;
};

// Дебаунсированный обработчик скролла
const debouncedHandleScroll = debounce(handleScroll, 150, {
  leading: true,
  trailing: true,
});

// Обработчики поиска
const handleSearch = async (query: string) => {
  try {
    if (!query) {
      logger.debug("Empty search query, loading all products");
      return loadProducts(false);
    }

    initialLoading.value = true;
    error.value = null;

    const result = await searchProducts(query);
    products.value = result.items;
    hasMore.value = products.value.length < result.total;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to search products";
    logger.error("Search failed", { query, error: err });
  } finally {
    initialLoading.value = false;
  }
};

const handleSearchClear = () => {
  logger.info("Search cleared");
  searchQuery.value = "";
  void loadProducts(false);
};

const handleSearchStateChange = (isActive: boolean) => {
  logger.debug("Search state changed", { isActive });
  setSearchActive(isActive);

  if (!isActive) {
    resetSearch();
    void loadProducts(false);
  }
};

// Обработчик клика по контенту
const handleContentClick = (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  const searchBar = searchBarRef.value?.$el;

  if (searchBar && !searchBar.contains(target) && !target.closest(".search-trigger")) {
    try {
      if (window.Telegram?.WebApp) {
        if (typeof window.Telegram.WebApp.closeScanQrPopup === "function") {
          window.Telegram.WebApp.closeScanQrPopup();
        }
        if (typeof window.Telegram.WebApp.hideKeyboard === "function") {
          window.Telegram.WebApp.hideKeyboard();
        }
      }
    } catch (err) {
      logger.debug("Telegram API call failed", { error: err });
    }

    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
    if (searchBarRef.value) {
      searchBarRef.value.blur();
    }
  }
};

// Обработчик выбора категории
const handleCategorySelect = (category: string) => {
  logger.info("Category selected", {
    category,
    currentCategory: selectedCategory.value,
  });

  if (category === selectedCategory.value) {
    selectedCategory.value = "";
  } else {
    selectedCategory.value = category;
  }

  currentPage.value = 1;
  void loadProducts(false);
};

// Обработчик добавления в корзину
const handleAddToCart = (product: IProduct) => {
  logger.info("Adding product to cart", {
    productId: product.id,
    productName: product.name,
  });
};

const resizeHandler = () => {
  if (productsContainer.value) {
    productsContainer.value.scrollTop = 0;
  }
};

// Хуки жизненного цикла
onMounted(() => {
  if (productsContainer.value) {
    productsContainer.value.addEventListener("scroll", debouncedHandleScroll);
    window.addEventListener("resize", resizeHandler);
  }

  // Выполняем первичную загрузку
  const initialLoad = async () => {
    try {
      // Сначала загружаем все категории
      await loadCategories();

      // Затем загружаем товары
      await loadProducts(false);

      // После загрузки проверяем необходимость подгрузки дополнительных товаров
      nextTick(() => {
        if (productsContainer.value && !hasVerticalScrollbar(productsContainer.value) && hasMore.value) {
          void handleScroll();
        }
      });
    } catch (err) {
      logger.error("Initial load failed", { error: err });
      // Если загрузка категорий не удалась, все равно пытаемся загрузить товары
      if (categories.value.length === 0) {
        await loadProducts(false);
      }
    }
  };

  void initialLoad();
});

onUnmounted(() => {
  if (productsContainer.value) {
    productsContainer.value.removeEventListener("scroll", debouncedHandleScroll);
  }

  window.removeEventListener("resize", resizeHandler);

  debouncedHandleScroll.cancel();
});

// Отслеживание состояния клавиатуры
watch(isKeyboardVisible, (visible) => {
  if (visible && productsContainer.value) {
    // Сохраняем текущую позицию скролла
    lastScrollPosition.value = productsContainer.value.scrollTop;
  } else {
    // Восстанавливаем позицию скролла после закрытия клавиатуры
    nextTick(() => {
      if (productsContainer.value) {
        productsContainer.value.scrollTop = lastScrollPosition.value;
      }
    });
  }
});

watch(selectedCategory, () => {
  void loadProducts(false);
});

watch(isKeyboardVisible, (visible) => {
  document.body.classList.toggle("keyboard-visible", visible);
});
</script>

<template>
  <div class="fixed-container">
    <div
      class="catalog-container"
      :class="{ 'keyboard-visible': isKeyboardVisible }"
      ref="productsContainer"
      @click="handleContentClick"
    >
      <!-- Фильтры -->
      <div class="filters-wrapper">
        <div
          class="catalog-filters"
          :class="{ 'search-active': isSearchActive }"
        >
          <div
            v-if="!isSearchActive"
            class="filters-spacer"
          ></div>
          
          <template v-if="!isSearchActive">
            <CategoryMenu
              :categories="categories"
              :selectedCategory="selectedCategory"
              @select="handleCategorySelect"
            />
          </template>
          
          <SearchBar
            ref="searchBarRef"
            v-model="searchQuery"
            :show-no-products="!products.length && !!searchQuery"
            @search="handleSearch"
            @clear="handleSearchClear"
            @searchStateChange="handleSearchStateChange"
          />
        </div>
      </div>

      <template v-if="!initialLoading">
        <!-- Сетка с товарами -->
        <div
          v-if="products.length > 0"
          class="products-grid"
        >
          <ProductCard
            v-for="product in products"
            :key="product.id"
            :product="product"
            @add-to-cart="handleAddToCart"
          />
        </div>

        <!-- Спиннер загрузки при подгрузке -->
        <div
          v-if="loadingMore"
          class="loading-more"
        >
          <LoadingSpinner />
        </div>
      </template>

      <!-- Спиннер начальной загрузки -->
      <div
        v-else
        class="initial-loading"
      >
        <LoadingSpinner />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Фиксированный внешний контейнер */
.fixed-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: var(--nav-height);
  overflow: hidden;
  z-index: 1;
}

/* Внутренний скроллируемый контейнер */
.catalog-container {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  /* Изменяем padding-bottom для корректного отступа */
  padding-bottom: calc((var(--keyboard-visible, 0) * var(--keyboard-height, 0) - var(--nav-height)));
  margin: 0 auto;
}

.loading-more {
  width: 100%;
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.initial-loading {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 0;
  left: 0;
}
</style>
