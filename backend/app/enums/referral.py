from enum import StrEnum, auto


class ReferralPayoutStatus(StrEnum):
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()
