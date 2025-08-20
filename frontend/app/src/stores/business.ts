import { DEFAULT_SORT_TYPE, SORT_TYPES } from "@/constants/sorting";
import { apiClient } from "@/services/httpClient.ts";
import type { IReferral, IReferralPayoutRequest } from "@/types/business.ts";
import type { UUID } from "@/types/common.ts";
import { logger } from "@/utils/logger.ts";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

export const useBusinessStore = defineStore("businessData", () => {
  // ==== UI STATE ====
  const itemColors = ["#BCCCFF", "#F8E058", "#FF92AD", "#4FE9F4", "#9CFFB2", "#E3C3FF"];

  const isConditionsModalOpen = ref(false);
  const isTermsModalOpen = ref(false);
  const isItemModalOpen = ref(false);
  const isAllPartnersModalOpen = ref(false);
  const isWithdrawModalOpen = ref(false);
  const isCopiedShown = ref(false);
  const isTopInvitedLoading = ref(false);
  const isReferralListLoading = ref(false);
  const wasAllPartnersModalOpen = ref(false); // флаг для отслеживания предыдущего состояния списка всех партнеров
  const hasSearchResults = ref(true); // флаг для отображения результатов поиска

  // ==== DATA STATE ====
  const profile = ref<IReferral | null>(null);
  const invitedUsers = ref<IReferral[]>([]);
  const topInvitedUsers = ref<IReferral[]>([]);
  const allMockInvitedUsers = ref<IReferral[]>([]); // Полный список моковых данных для поиска
  const totalInvited = ref(0);
  const page = ref(1);
  const pageSize = ref(50);

  const selectedReferral = ref<IReferral | null>(null);
  const selectedChildren = ref<IReferral[]>([]);
  const selectedTotalChildren = ref(0);
  const selectedPage = ref(1);

  // ==== COMPUTED ====
  const balance = computed(() => profile.value?.balance ?? 0);
  const linkToShare = computed(() => profile.value?.invite_link ?? "");
  const signedConditions = computed(() => profile.value?.signed_conditions ?? false);
  const signedTerms = computed(() => profile.value?.signed_user_terms ?? false);
  const isRegistered = computed(() => profile.value?.is_registered ?? false);
  const isAbleToWithdraw = computed(() => isRegistered.value && balance.value > 0);

  // ==== HELPERS ====
  const getRandomItemColor = () => itemColors[Math.floor(Math.random() * itemColors.length)];

  const getItemsWithColor = (items: IReferral[]): IReferral[] => {
    return items.map((item) => {
      const color = getRandomItemColor();
      return { ...item, item_color: color };
    });
  };

  function getRandomInt(min: number, max: number): number {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function getRandomName(): string {
    const firstNames = ["Иван", "Пётр", "Сергей", "Алексей", "Дмитрий"];
    const lastNames = ["Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов"];

    const fn = firstNames[Math.floor(Math.random() * firstNames.length)];
    const ln = lastNames[Math.floor(Math.random() * lastNames.length)];
    return `${fn} ${ln}`;
  }

  const generateMockData = (amount: number, startId: number = 0) => {
    const mockItems: IReferral[] = [];
    for (let i = 0; i < amount; i++) {
      mockItems.push({
        id: (startId + i).toString(),
        full_name: getRandomName(),
        referral_bonus: getRandomInt(0, 70_000),
        referrals_count: getRandomInt(0, 5000),
        current_month_orders: getRandomInt(0, 100),
        item_color: getRandomItemColor(),
      });
    }
    return mockItems;
  };

  // ==== ACTIONS ====
  const fetchProfile = async () => {
    try {
      logger.info("Fetching referral profile");
      profile.value = await apiClient.get<IReferral>("/referral/me");
      profile.value.item_color = getRandomItemColor();
    } catch (error) {
      logger.error("Failed to fetch referral profile", { error });
      throw error;
    }
  };

  const fetchInvited = async () => {
    try {
      logger.info("Fetching invited users", { page: page.value });
      const res = await apiClient.get<{ items: IReferral[]; total: number }>("/referral/me/children", {
        page: page.value,
        page_size: pageSize.value,
      });

      // Если это первая страница, очищаем предыдущие данные
      if (page.value === 1) {
        invitedUsers.value = getItemsWithColor(res.items);
      } else {
        invitedUsers.value = [...invitedUsers.value, ...getItemsWithColor(res.items)];
      }

      totalInvited.value = res.total;
      hasSearchResults.value = true; // При обычной загрузке всегда есть результаты

      // mock data
      const mockData = generateMockData(pageSize.value);
      if (page.value === 1) {
        // Генерируем полный список моковых данных для поиска
        allMockInvitedUsers.value = generateMockData(100); // Генерируем больше данных для поиска
        invitedUsers.value = [...invitedUsers.value, ...mockData];
      } else {
        invitedUsers.value = [...invitedUsers.value, ...mockData];
      }
      totalInvited.value = 100;
    } catch (error) {
      logger.error("Failed to fetch invited users", { error });
      throw error;
    }
  };

  const fetchChildren = async (referralId: UUID) => {
    try {
      logger.info("Fetching referral children", { page: selectedPage.value });
      const resp = await apiClient.get<{ items: IReferral[]; total: number }>(
        `/referral/${referralId}/children`,
        { page: selectedPage.value, page_size: pageSize.value },
      );
      selectedChildren.value = [...selectedChildren.value, ...getItemsWithColor(resp.items)];
      selectedTotalChildren.value = resp.total;

      // mock data
      selectedChildren.value = [...selectedChildren.value, ...generateMockData(pageSize.value)];
      selectedTotalChildren.value = 100;
    } catch (error) {
      logger.error("Failed to fetch referral children", { error });
      throw error;
    }
  };

  const fetchTopInvited = async () => {
    try {
      logger.info("Fetching top invited users", { page: page.value });
      isTopInvitedLoading.value = true;
      const res = await apiClient.get<{ items: IReferral[]; total: number }>("/referral/me/children/top", {
        page: page.value,
        page_size: pageSize.value,
      });
      topInvitedUsers.value = getItemsWithColor(res.items);
      totalInvited.value = res.total;

      // mock data gen
      topInvitedUsers.value.push(...generateMockData(10));
      totalInvited.value = 100;

      topInvitedUsers.value = topInvitedUsers.value.slice(0, 10);
    } catch (error) {
      logger.error("Failed to fetch top invited users", { error });
      throw error;
    } finally {
      isTopInvitedLoading.value = false;
    }
  };

  const searchInvited = async (name: string) => {
    try {
      logger.info("Searching invited users locally", { name, page: 1 });
      page.value = 1;

      /*
      // Фактический запрос к серверу для поиска должен быть таким:
        const res = await apiClient.post<{ items: IReferral[]; total: number }>(
        '/referral/me/children/search',
        {},
        { params: { name, page: page.value, page_size: pageSize.value } },
      */

      // Поиск по моковым данным
      const filteredResults = allMockInvitedUsers.value.filter((user) =>
        user.full_name.toLowerCase().includes(name.toLowerCase()),
      );

      invitedUsers.value = getItemsWithColor(filteredResults);
      totalInvited.value = filteredResults.length;
      hasSearchResults.value = filteredResults.length > 0;

      logger.info("Local search completed", {
        query: name,
        resultsCount: filteredResults.length,
      });
    } catch (error) {
      logger.error("Failed to search invited users locally", { error });
      hasSearchResults.value = false;
      throw error;
    }
  };

  const sortInvited = (sortType: string) => {
    logger.info("Sorting invited users", { sortType });

    if (sortType === SORT_TYPES.HIGHEST_BONUS) {
      invitedUsers.value = [...invitedUsers.value].sort((a, b) => b.referral_bonus - a.referral_bonus);
      // Также сортируем полный список моковых данных для консистентности
      if (allMockInvitedUsers.value.length > 0) {
        allMockInvitedUsers.value = [...allMockInvitedUsers.value].sort(
          (a, b) => b.referral_bonus - a.referral_bonus,
        );
      }
    } else if (sortType === SORT_TYPES.NEWEST) {
      // Сортируем по id в убывающем порядке (предполагая что id растет со временем)
      invitedUsers.value = [...invitedUsers.value].sort((a, b) => b.id.localeCompare(a.id));
      // Также сортируем полный список моковых данных для консистентности
      if (allMockInvitedUsers.value.length > 0) {
        allMockInvitedUsers.value = [...allMockInvitedUsers.value].sort((a, b) => b.id.localeCompare(a.id));
      }
    }
  };

  const loadMoreInvited = async () => {
    const maxPage = Math.ceil(totalInvited.value / pageSize.value);
    if (page.value >= maxPage) return;

    page.value++;

    // Если используем моковые данные для поиска, загружаем следующую страницу из них
    if (allMockInvitedUsers.value.length > 0) {
      const startIndex = (page.value - 1) * pageSize.value;
      const endIndex = page.value * pageSize.value;
      const nextPageData = allMockInvitedUsers.value.slice(startIndex, endIndex);

      if (nextPageData.length > 0) {
        invitedUsers.value = [...invitedUsers.value, ...getItemsWithColor(nextPageData)];
      }
    } else {
      await fetchInvited();
    }
  };

  const loadMoreChildren = async (referralId: UUID) => {
    const maxPage = Math.ceil(selectedTotalChildren.value / pageSize.value);
    if (selectedPage.value >= maxPage) return;

    selectedPage.value++;
    await fetchChildren(referralId);
  };

  const openReferralDetails = async (referralId: UUID) => {
    try {
      logger.info("Opening referral details", { referralId });
      // Запоминаем, было ли открыто модальное окно со всеми партнерами
      wasAllPartnersModalOpen.value = isAllPartnersModalOpen.value;
      // Скрываем модальное окно со всеми партнерами
      isAllPartnersModalOpen.value = false;
      // Открываем детальное модальное окно
      isItemModalOpen.value = true;
      selectedPage.value = 1;

      selectedReferral.value = await apiClient.get<IReferral>(`/referral/${referralId}`);
      selectedReferral.value.item_color = getRandomItemColor();

      await fetchChildren(referralId);
    } catch (error) {
      logger.error("Failed to open referral details", { error, referralId });
      throw error;
    }
  };

  const openAllReferrals = async () => {
    logger.info("Opening all referrals modal");
    isAllPartnersModalOpen.value = true;
    page.value = 1;

    // Если у нас еще нет моковых данных, загружаем их
    if (allMockInvitedUsers.value.length === 0) {
      await fetchInvited();
    } else {
      // Восстанавливаем первую страницу из уже имеющихся моковых данных
      const firstPageData = allMockInvitedUsers.value.slice(0, pageSize.value);
      invitedUsers.value = getItemsWithColor(firstPageData);
      totalInvited.value = allMockInvitedUsers.value.length;
    }

    // Применяем сортировку по умолчанию
    sortInvited(DEFAULT_SORT_TYPE);
  };

  const closeAllReferrals = () => {
    logger.info("Closing all referrals modal");
    isAllPartnersModalOpen.value = false;
    wasAllPartnersModalOpen.value = false;
    invitedUsers.value = [];
    hasSearchResults.value = true;
    page.value = 1;
    // Сохраняем моковые данные, чтобы не перегенерировать их при следующем открытии
  };

  const resetSearchState = () => {
    hasSearchResults.value = true;
    page.value = 1;
    invitedUsers.value = [];
    // Восстанавливаем первую порцию данных из полного списка моковых данных
    if (allMockInvitedUsers.value.length > 0) {
      const firstPageData = allMockInvitedUsers.value.slice(0, pageSize.value);
      invitedUsers.value = getItemsWithColor(firstPageData);
      totalInvited.value = allMockInvitedUsers.value.length;
    }
  };

  const closeReferralDetails = () => {
    logger.info("Closing referral details modal");
    isItemModalOpen.value = false;
    selectedReferral.value = null;
    selectedChildren.value = [];
  };

  const closeReferralDetailsAndReturnToAll = () => {
    logger.info("Closing referral details modal and returning to all partners");
    isItemModalOpen.value = false;
    selectedReferral.value = null;
    selectedChildren.value = [];
    // Возвращаемся к модальному окну со всеми партнерами, если оно было открыто
    if (wasAllPartnersModalOpen.value) {
      isAllPartnersModalOpen.value = true;
      wasAllPartnersModalOpen.value = false;
    }
  };

  const sendWithdrawRequest = async (data: IReferralPayoutRequest) => {
    try {
      await apiClient.post<IReferral>(`/referral/payout-request`, data);
    } catch (error) {
      logger.error("Failed to make a withdrawal request", { error });
      throw error;
    }
  };

  const openWithdrawModal = () => {
    isWithdrawModalOpen.value = true;
  };

  const onSendWithdrawRequest = async (data: IReferralPayoutRequest) => {
    await sendWithdrawRequest(data);
    isWithdrawModalOpen.value = false;
  };

  // ==== SIGN ACTIONS ====
  const signConditions = async () => {
    try {
      logger.info("Signing referral conditions");
      if (!profile.value) await fetchProfile();
      profile.value = await apiClient.post<IReferral>("/referral/me/sign_conditions");
      logger.info("Conditions signed");
    } catch (error) {
      logger.error("Failed to sign conditions", { error });
      throw error;
    }
  };

  const signUserTerms = async () => {
    try {
      logger.info("Signing referral user terms");
      if (!profile.value) await fetchProfile();
      profile.value = await apiClient.post<IReferral>("/referral/me/sign_user_terms");
      logger.info("User terms signed");
    } catch (error) {
      logger.error("Failed to sign user terms", { error });
      throw error;
    }
  };

  // модалки условий
  const openConditionsFlow = () => {
    logger.info("Opening conditions modal");
    isConditionsModalOpen.value = true;
  };
  const confirmConditions = async () => {
    await signConditions();
    logger.info("Confirmed conditions, opening terms modal");
    isConditionsModalOpen.value = false;
    isTermsModalOpen.value = true;
  };
  const confirmTerms = async (callback?: () => void) => {
    await signUserTerms();
    logger.info("Confirmed user terms");
    isTermsModalOpen.value = false;
    callback?.();
  };
  const openTermsDirectly = () => {
    logger.info("Opening terms modal directly");
    isTermsModalOpen.value = true;
  };

  // копирование реф-ссылки
  const copyLink = () => {
    navigator.clipboard.writeText(linkToShare.value);
    isCopiedShown.value = true;
    logger.info("Copied referral link to clipboard", { link: linkToShare.value });
    setTimeout(() => (isCopiedShown.value = false), 2000);
  };

  return {
    // UI state
    isConditionsModalOpen,
    isTermsModalOpen,
    isItemModalOpen,
    isAllPartnersModalOpen,
    isCopiedShown,
    isTopInvitedLoading,
    isReferralListLoading,
    isWithdrawModalOpen,
    hasSearchResults,

    // Data state
    profile,
    invitedUsers,
    totalInvited,
    topInvitedUsers,
    page,
    pageSize,
    selectedReferral,
    selectedChildren,
    selectedPage,
    linkToShare,

    // Computed
    balance,
    signedConditions,
    signedTerms,
    isRegistered,
    isAbleToWithdraw,

    // Helpers
    getRandomItemColor,
    getItemsWithColor,

    // Actions
    fetchProfile,
    fetchInvited,
    fetchTopInvited,
    fetchChildren,
    searchInvited,
    sortInvited,
    resetSearchState,
    loadMoreInvited,
    loadMoreChildren,
    openReferralDetails,
    openAllReferrals,
    closeAllReferrals,
    closeReferralDetails,
    closeReferralDetailsAndReturnToAll,

    openConditionsFlow,
    confirmConditions,
    confirmTerms,
    openTermsDirectly,

    openWithdrawModal,
    sendWithdrawRequest,
    onSendWithdrawRequest,

    signConditions,
    signUserTerms,

    copyLink,
  };
});
