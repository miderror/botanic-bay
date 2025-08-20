<script setup lang="ts">
import ProductEditModal from "@/components/admin/ProductEditModal.vue";
import LoadingSpinner from "@/components/common/LoadingSpinner.vue";
import NotificationToast from "@/components/common/NotificationToast.vue";
import { useNotification } from "@/composables/useNotification";
import { ADMIN_PRODUCTS_PER_PAGE } from "@/config/pagination";
import { adminService } from "@/services/adminService";
import type { IAdminProduct } from "@/types/admin";
import { formatPrice } from "@/utils/formatters";
import { logger } from "@/utils/logger";
import { debounce } from "lodash-es";
import { onMounted, ref, watch } from "vue";

// Состояние
const products = ref<IAdminProduct[]>([]);
const categories = ref<string[]>([]);
const currentPage = ref(1);
const totalPages = ref(1);
const isLoading = ref(false);

// Модальное окно
const showProductModal = ref(false);
const selectedProduct = ref<IAdminProduct | null>(null);

// Уведомления
const { message, type, show, showNotification } = useNotification();

// Фильтры
const filters = ref({
  name: "",
  category: "",
  // По умолчанию показываем только активные товары (is_active = true)
  showInactive: false,
});

// Загрузка всех категорий
const loadAllCategories = async () => {
  try {
    // Используем существующий метод getCategories из adminService
    const allCategories = await adminService.getCategories();
    categories.value = allCategories;

    logger.info("All product categories loaded", {
      categoriesCount: categories.value.length,
    });
  } catch (error) {
    logger.error("Failed to load all categories", { error });
    showNotification("Не удалось загрузить категории", "error");
  }
};

// Загрузка товаров
const loadProducts = async () => {
  try {
    isLoading.value = true;

    // Формируем объект с параметрами для API
    const apiFilters = {
      name: filters.value.name,
      category: filters.value.category,
      // Если showInactive = false, то передаем фильтр is_active=true
      // Если showInactive = true, то не передаем фильтр is_active вообще
      // (чтобы получить и активные, и неактивные)
      ...(filters.value.showInactive ? {} : { is_active: true }),
    };

    const response = await adminService.getProducts(currentPage.value, ADMIN_PRODUCTS_PER_PAGE, apiFilters);

    products.value = response.items;
    totalPages.value = response.pages;

    logger.info("Products loaded for admin", {
      page: currentPage.value,
      total: response.total,
      filters: apiFilters,
    });
  } catch (error) {
    logger.error("Failed to load products", { error });
    showNotification("Не удалось загрузить список товаров", "error");
  } finally {
    isLoading.value = false;
  }
};

// Методы для работы с модальным окном
const openProductModal = (product?: IAdminProduct) => {
  selectedProduct.value = product || null;
  showProductModal.value = true;
};

const closeProductModal = () => {
  selectedProduct.value = null;
  showProductModal.value = false;
};

// Сохранение товара
const saveProduct = async (productData: IAdminProduct) => {
  try {
    if (productData.id) {
      // Обновление существующего товара
      await adminService.updateProduct(productData.id, productData);
      showNotification("Товар успешно обновлен", "success");
    } else {
      // Создание нового товара
      await adminService.createProduct(productData);
      showNotification("Товар успешно создан", "success");
    }

    await loadProducts(); // Перезагружаем список
    closeProductModal();
  } catch (error) {
    logger.error("Failed to save product", { error });
    showNotification("Не удалось сохранить товар", "error");
  }
};

// Удаление товара
const confirmDeleteProduct = (product: IAdminProduct) => {
  if (confirm(`Вы действительно хотите удалить товар "${product.name}"?`)) {
    deleteProduct(product.id);
  }
};

const deleteProduct = async (productId: string) => {
  try {
    await adminService.deleteProduct(productId);
    showNotification("Товар успешно удален", "success");
    await loadProducts(); // Перезагружаем список
  } catch (error) {
    logger.error("Failed to delete product", { error });
    showNotification("Не удалось удалить товар", "error");
  }
};

// Пагинация
const changePage = async (newPage: number) => {
  try {
    if (newPage < 1 || newPage > totalPages.value) return;
    currentPage.value = newPage;
    await loadProducts();
  } catch (error) {
    logger.error("Failed to change page", { error });
    showNotification("Не удалось загрузить страницу", "error");
  }
};

// Обработка фильтров с debounce
const handleFilterChange = debounce(async () => {
  try {
    currentPage.value = 1; // Сбрасываем страницу при изменении фильтров
    await loadProducts();
  } catch (error) {
    logger.error("Failed to apply filters", { error });
    showNotification("Не удалось применить фильтры", "error");
  }
}, 300);

// Следим за изменениями фильтров и страницы
watch(
  [currentPage, () => ({ ...filters.value })],
  async () => {
    try {
      await loadProducts();
    } catch (error) {
      logger.error("Failed to load products after filters/page change", { error });
    }
  },
  { deep: true },
);

// Инициализация
onMounted(() => {
  loadAllCategories();
  loadProducts();
});
</script>

<template>
  <div class="admin-products">
    <div class="admin-header">
      <h1>Управление товарами</h1>
      <button
        class="admin-add-button"
        @click="openProductModal()"
      >
        Добавить товар
      </button>
    </div>

    <!-- Фильтры -->
    <div class="admin-filters">
      <div class="admin-filter-group">
        <input
          v-model="filters.name"
          type="text"
          placeholder="Поиск по названию"
          class="admin-filter-input"
          @input="handleFilterChange"
        />

        <select
          v-model="filters.category"
          class="admin-filter-select"
          @change="handleFilterChange"
        >
          <option value="">Все категории</option>
          <option
            v-for="category in categories"
            :key="category"
            :value="category"
          >
            {{ category }}
          </option>
        </select>
      </div>

      <div class="admin-filter-group">
        <div class="admin-filter-checkbox">
          <input
            type="checkbox"
            v-model="filters.showInactive"
            id="show-inactive"
            @change="handleFilterChange"
            class="admin-checkbox"
          />
          <label
            for="show-inactive"
            class="admin-checkbox-label"
          >
            Показывать неактивные товары
          </label>
        </div>
      </div>
    </div>

    <!-- Таблица товаров -->
    <div class="admin-table-container">
      <template v-if="isLoading">
        <div class="admin-loading-spinner">
          <LoadingSpinner />
        </div>
      </template>

      <template v-else-if="products.length === 0">
        <div class="admin-empty-state">
          <p>Товары не найдены</p>
        </div>
      </template>

      <template v-else>
        <table class="admin-table">
          <thead>
            <tr>
              <th>Название</th>
              <th>Категория</th>
              <th>Цена</th>
              <th>Остаток</th>
              <th>Статус</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="product in products"
              :key="product.id"
            >
              <td>{{ product.name }}</td>
              <td>{{ product.category }}</td>
              <td>{{ formatPrice(product.price) }}</td>
              <td>{{ product.stock }}</td>
              <td>
                <span
                  class="admin-status-badge"
                  :class="{
                    'admin-status-active': product.is_active,
                    'admin-status-inactive': !product.is_active,
                  }"
                >
                  {{ product.is_active ? "Активен" : "Неактивен" }}
                </span>
              </td>
              <td class="admin-actions">
                <button
                  class="admin-action-btn edit"
                  @click="openProductModal(product)"
                >
                  Редактировать
                </button>
                <button
                  class="admin-action-btn delete"
                  @click="confirmDeleteProduct(product)"
                >
                  Удалить
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </template>
    </div>

    <!-- Пагинация -->
    <div class="admin-pagination">
      <button
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
        class="admin-page-btn"
      >
        ←
      </button>
      <span class="admin-page-info"> Страница {{ currentPage }} из {{ totalPages }} </span>
      <button
        :disabled="currentPage === totalPages"
        @click="changePage(currentPage + 1)"
        class="admin-page-btn"
      >
        →
      </button>
    </div>

    <!-- Модальное окно редактирования товара -->
    <ProductEditModal
      v-if="showProductModal"
      :product="selectedProduct"
      :categories="categories"
      @close="closeProductModal"
      @save="saveProduct"
    />

    <!-- Уведомления -->
    <NotificationToast
      :show="show"
      :message="message"
      :type="type"
    />
  </div>
</template>

<style>
@import "@/assets/styles/admin.css";
</style>
