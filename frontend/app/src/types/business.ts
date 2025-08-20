import type { UUID } from "./common";

export enum ReferralPayoutStatus {
  PENDING = "pending",
  APPROVED = "approved",
  REJECTED = "rejected",
}

export interface IReferral {
  id: UUID;
  full_name: string;
  balance?: number;
  referral_bonus: number;
  is_registered?: boolean;
  referrals_count?: number;
  signed_conditions?: boolean;
  signed_user_terms?: boolean;
  current_month_orders?: number;
  invite_link?: string;
  item_color?: string;
}

export interface IReferrer {
  id: UUID;
  full_name: string;
}

export interface IReferralPayoutRequest {
  id?: UUID;
  bank_code: string;
  account_number: string;
  amount: number;
  status?: ReferralPayoutStatus;
  referrer_id?: UUID;
  referrer?: IReferrer;
  created_at?: string;
}
