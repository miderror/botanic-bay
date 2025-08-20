import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import CatalogView from "../views/CatalogView.vue";

const adminGuard = async () => {
  const authStore = useAuthStore();

  if (!authStore.isAdmin) {
    return "/";
  }
};

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      redirect: "/catalog",
    },
    {
      path: "/cart",
      name: "cart",
      component: () => import("@/components/cart/CartView.vue"),
    },
    {
      path: "/payment/success",
      name: "payment-success",
      component: () => import("@/views/PaymentResultView.vue"),
    },
    {
      path: "/payment/result/:orderId?",
      name: "payment-result",
      component: () => import("@/views/PaymentResultView.vue"),
      props: true,
    },
    {
      path: "/catalog",
      name: "catalog",
      component: CatalogView,
    },
    {
      path: "/admin",
      name: "admin",
      component: () => import("@/views/admin/AdminView.vue"),
      beforeEnter: adminGuard,
      children: [
        {
          path: "", // Пустой путь
          name: "admin-default", // Добавляем имя!
          redirect: "/admin/products",
        },
        {
          path: "products",
          name: "admin-products",
          component: () => import("@/views/admin/ProductsView.vue"),
        },
        {
          path: "users",
          name: "admin-users",
          component: () => import("@/views/admin/UsersView.vue"),
        },
        {
          path: "orders",
          name: "admin-orders",
          component: () => import("@/views/admin/OrdersView.vue"),
        },
        {
          path: "payout-requests",
          name: "admin-payout-requests",
          component: () => import("@/views/admin/PayoutRequestsView.vue"),
        },
      ],
    },
    {
      path: "/orders",
      name: "orders",
      component: () => import("@/views/OrdersView.vue"),
      children: [
        {
          path: "",
          name: "orders-default", // Добавляем имя!
          redirect: { name: "orders-list" },
        },
        {
          path: "cart",
          name: "orders-cart",
          component: () => import("@/components/cart/CartView.vue"),
        },
        {
          path: "list",
          name: "orders-list",
          component: () => import("@/components/orders/OrderList.vue"),
        },
        {
          path: ":id",
          name: "order-details",
          component: () => import("@/components/orders/OrderDetails.vue"),
          props: true,
        },
      ],
    },
    {
      path: "/profile",
      name: "profile",
      component: () => import("@/views/ProfileView.vue"),
      children: [
        {
          path: "",
          name: "profile-default", // Добавляем имя!
          redirect: { name: "profile-orders" },
        },
        {
          path: "orders",
          name: "profile-orders",
          component: () => import("@/components/profile/OrderHistory.vue"),
        },
        {
          path: "business",
          name: "profile-business",
          component: () => import("@/components/profile/BusinessView.vue"),
        },
        {
          path: "account",
          name: "profile-account",
          component: () => import("@/components/profile/AccountData.vue"),
        },
      ],
    },
  ],
});

router.beforeEach((to, from, next) => {
  const code = to.query?.referral_code;
  if (typeof code === "string" && !localStorage.getItem("referral_code")) {
    localStorage.setItem("referral_code", code);
    console.info("[referral] saved code", code);
  }
  next();
});

export default router;
