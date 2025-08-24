// frontend/app/src/stores/business.ts

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { apiClient } from "@/services/httpClient.ts";
import type { IReferral, IReferralPayoutRequest } from "@/types/business.ts";
import type { UUID } from "@/types/common.ts";
import { logger } from "@/utils/logger.ts";
import { DEFAULT_SORT_TYPE, type SortType } from "@/constants/sorting";

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
  const wasAllPartnersModalOpen = ref(false);
  const hasSearchResults = ref(true);

  // ==== DATA STATE ====
  const profile = ref<IReferral | null>(null);
  const invitedUsers = ref<IReferral[]>([]);
  const topInvitedUsers = ref<IReferral[]>([]);
  const totalInvited = ref(0);
  const page = ref(1);
  const pageSize = ref(50);
  const hasMoreInvited = ref(true);

  const selectedReferral = ref<IReferral | null>(null);
  const selectedChildren = ref<IReferral[]>([]);
  const selectedTotalChildren = ref(0);
  const selectedPage = ref(1);
  const hasMoreChildren = ref(true);

  // ==== COMPUTED ====

  const balance = computed(() => profile.value?.total_balance ?? 0);
  const linkToShare = computed(() => profile.value?.invite_link ?? "");
  const signedConditions = computed(() => profile.value?.signed_conditions ?? false);
  const signedTerms = computed(() => profile.value?.signed_user_terms ?? false);
  const isRegistered = computed(() => profile.value?.is_registered ?? false);
  const isAbleToWithdraw = computed(() => isRegistered.value && balance.value > 0);

  // ==== HELPERS ====
  const getRandomItemColor = () => itemColors[Math.floor(Math.random() * itemColors.length)];

  const getItemsWithColor = (items: IReferral[]): IReferral[] => {
    return items.map((item) => ({ ...item, item_color: getRandomItemColor() }));
  };

  // ==== ACTIONS ====
  const fetchProfile = async () => {
    try {
      logger.info("Fetching referral profile");
      profile.value = await apiClient.get<IReferral>("/referral/me");
    } catch (error) {
      logger.error("Failed to fetch referral profile", { error });
      throw error;
    }
  };

  const fetchInvited = async (sortType: SortType = DEFAULT_SORT_TYPE) => {
    if (isReferralListLoading.value) return;
    try {
      isReferralListLoading.value = true;
      logger.info("Fetching invited users", { page: page.value, sortType });

      const res = await apiClient.get<{ items: IReferral[]; total: number; pages: number }>(
        "/referral/me/children",
        {
          page: page.value,
          page_size: pageSize.value,
          sort_by: sortType,
        },
      );

      const newItems = getItemsWithColor(res.items);
      if (page.value === 1) {
        invitedUsers.value = newItems;
      } else {
        invitedUsers.value = [...invitedUsers.value, ...newItems];
      }

      totalInvited.value = res.total;
      hasMoreInvited.value = page.value < res.pages;
      hasSearchResults.value = true;
    } catch (error) {
      logger.error("Failed to fetch invited users", { error });
      throw error;
    } finally {
      isReferralListLoading.value = false;
    }
  };

  const fetchChildren = async (referralId: UUID) => {
    if (isReferralListLoading.value) return;
    try {
      isReferralListLoading.value = true;
      logger.info("Fetching referral children", { referralId, page: selectedPage.value });
      const resp = await apiClient.get<{ items: IReferral[]; total: number; pages: number }>(
        `/referral/${referralId}/children`,
        { page: selectedPage.value, page_size: pageSize.value },
      );

      const newItems = getItemsWithColor(resp.items);
      if (selectedPage.value === 1) {
        selectedChildren.value = newItems;
      } else {
        selectedChildren.value = [...selectedChildren.value, ...newItems];
      }

      selectedTotalChildren.value = resp.total;
      hasMoreChildren.value = selectedPage.value < resp.pages;
    } catch (error) {
      logger.error("Failed to fetch referral children", { error });
      throw error;
    } finally {
      isReferralListLoading.value = false;
    }
  };
  
  const fetchTopInvited = async () => {
    try {
      isTopInvitedLoading.value = true;
      const res = await apiClient.get<{ items: IReferral[] }>("/referral/me/children/top");
      topInvitedUsers.value = getItemsWithColor(res.items);
    } catch (error) {
      logger.error("Failed to fetch top invited users", { error });
    } finally {
      isTopInvitedLoading.value = false;
    }
  };

  const searchInvited = async (name: string) => {
    try {
      isReferralListLoading.value = true;
      logger.info("Searching invited users", { name, page: 1 });
      page.value = 1;
  
      const res = await apiClient.post<{ items: IReferral[]; total: number; pages: number }>(
        '/referral/me/children/search',
        {},
        { params: { name, page: page.value, page_size: pageSize.value } },
      );
  
      invitedUsers.value = getItemsWithColor(res.items);
      totalInvited.value = res.total;
      hasMoreInvited.value = page.value < res.pages;
      hasSearchResults.value = res.items.length > 0;
    } catch (error) {
      logger.error("Failed to search invited users", { error });
      hasSearchResults.value = false;
      throw error;
    } finally {
      isReferralListLoading.value = false;
    }
  };

  const sortInvited = (sortType: SortType) => {
      page.value = 1;
      fetchInvited(sortType);
  };
  
  const loadMoreInvited = async () => {
    if (hasMoreInvited.value && !isReferralListLoading.value) {
      page.value++;
      await fetchInvited();
    }
  };

  const loadMoreChildren = async (referralId: UUID) => {
    if (hasMoreChildren.value && !isReferralListLoading.value) {
      selectedPage.value++;
      await fetchChildren(referralId);
    }
  };

  const openReferralDetails = async (referralId: UUID) => {
    try {
      logger.info("Opening referral details", { referralId });
      wasAllPartnersModalOpen.value = isAllPartnersModalOpen.value;
      isAllPartnersModalOpen.value = false;
      isItemModalOpen.value = true;
      selectedPage.value = 1;
      selectedChildren.value = [];

      selectedReferral.value = await apiClient.get<IReferral>(`/referral/${referralId}`);
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
    await fetchInvited();
  };

  const closeAllReferrals = () => {
    logger.info("Closing all referrals modal");
    isAllPartnersModalOpen.value = false;
    wasAllPartnersModalOpen.value = false;
    invitedUsers.value = [];
    hasSearchResults.value = true;
    page.value = 1;
  };

  const resetSearchState = async () => {
    hasSearchResults.value = true;
    page.value = 1;
    await fetchInvited();
  };

  const closeReferralDetailsAndReturnToAll = () => {
    logger.info("Closing referral details modal and returning to all partners");
    isItemModalOpen.value = false;
    selectedReferral.value = null;
    selectedChildren.value = [];
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

  const copyLink = () => {
    navigator.clipboard.writeText(linkToShare.value);
    isCopiedShown.value = true;
    logger.info("Copied referral link to clipboard", { link: linkToShare.value });
    setTimeout(() => (isCopiedShown.value = false), 2000);
  };

  return {
    isConditionsModalOpen, isTermsModalOpen, isItemModalOpen, isAllPartnersModalOpen,
    isCopiedShown, isTopInvitedLoading, isReferralListLoading, isWithdrawModalOpen,
    hasSearchResults, profile, invitedUsers, totalInvited, topInvitedUsers,
    page, pageSize, selectedReferral, selectedChildren, selectedPage, linkToShare,
    balance, signedConditions, signedTerms, isRegistered, isAbleToWithdraw,
    getRandomItemColor, getItemsWithColor, fetchProfile, fetchInvited,
    fetchTopInvited, fetchChildren, searchInvited, sortInvited, resetSearchState,
    loadMoreInvited, loadMoreChildren, openReferralDetails, openAllReferrals,
    closeAllReferrals, closeReferralDetailsAndReturnToAll, openConditionsFlow,
    confirmConditions, confirmTerms, openTermsDirectly, openWithdrawModal,
    sendWithdrawRequest, onSendWithdrawRequest, signConditions, signUserTerms, copyLink,
  };
});