import { ref } from "vue";

export function useReferralCode() {
  const referralCode = ref<string | null>(localStorage.getItem("referral_code"));
  return { referralCode };
}
