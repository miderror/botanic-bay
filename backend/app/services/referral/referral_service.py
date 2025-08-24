import base64
import math
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional, Tuple
from uuid import UUID

from aiogram.utils.deep_linking import create_start_link
from fastapi import HTTPException, status
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.core.settings import settings
from app.crud.order import OrderCRUD
from app.crud.payout_request import PayoutRequestCRUD
from app.crud.referral import ReferralCRUD
from app.crud.referral_bonus import ReferralBonusCRUD
from app.crud.user import UserCRUD
from app.enums.referral import ReferralPayoutStatus
from app.models import Order, User
from app.models.order_status import OrderStatus
from app.schemas.referral import (
    ReferralLinkPayload,
    SReferral,
    SReferralListPaginated,
    SReferralPayoutRequest,
    SReferralPayoutRequestPaginated,
    SReferrer,
)
from app.services.telegram.bot_manager import TelegramBotManager


class ReferralService:
    """Сервис для работы с рефералами"""

    def __init__(
        self,
        bot_manager: TelegramBotManager,
        referral_crud: ReferralCRUD,
        referral_bonus_crud: ReferralBonusCRUD,
        order_crud: OrderCRUD,
        payout_request_crud: PayoutRequestCRUD,
        session: AsyncSession,
    ):
        self.bot_manager = bot_manager
        self.referral_crud = referral_crud
        self.referral_bonus_crud = referral_bonus_crud
        self.order_crud = order_crud
        self.payout_request_crud = payout_request_crud
        self.session = session
        self.user_crud = UserCRUD(session)

    async def get_invite_link(
        self,
        *,
        user_id: Optional[UUID] = None,
        referral_id: Optional[UUID] = None,
    ) -> str:
        if referral_id is None and user_id is None:
            raise ValueError(
                "Either user_id or referral_id must be set to get an invite link!"
            )

        referral = await self.referral_crud.get_or_create(
            user_id=user_id,
            referral_id=referral_id,
        )

        payload = ReferralLinkPayload(referral_code=referral.user.referral_code)
        data = payload.model_dump_json()

        return await create_start_link(
            bot=self.bot_manager.bot,
            payload=data,
            encode=True,
        )

    async def save_referral(
        self,
        referrer_user_id: UUID,
        referral_user_id: UUID,
    ):
        extra = {
            "user_id": referrer_user_id,
            "referral_user_id": referral_user_id,
        }
        logger.info(
            "Saving new referral for the user",
            extra=extra,
        )

        if not (await self.referral_crud.get(user_id=referral_user_id)):
            referrer = await self.referral_crud.get(user_id=referrer_user_id)
            await self.referral_crud.create(referral_user_id, referrer.id)

            logger.info(
                "Saved new referral for the user",
                extra=extra,
            )

        raise HTTPException(
            status_code=status.HTTP_417_EXPECTATION_FAILED,
            detail="The referral record for the user already exists",
        )

    async def apply_referral_bonus(self, order: Order) -> None:
        if order.status != OrderStatus.PAID.value:
            logger.warning(
                "Order is not paid, skipping referral bonus",
                extra={"order_id": str(order.id)},
            )
            return

        referral = await self.referral_crud.get(user_id=order.user_id)
        if not referral or not referral.referrer_id:
            logger.info(
                "User has no referrer, skipping bonus",
                extra={"user_id": str(order.user_id)},
            )
            return

        current_referrer_id = referral.referrer_id
        level = 1

        async with self.session.begin_nested():
            while current_referrer_id and level <= settings.REFERRAL_MAX_LEVEL:
                parent_referral = await self.referral_crud.get(
                    referral_id=current_referrer_id
                )
                if not parent_referral:
                    break

                percent = settings.REFERRAL_LEVELS.get(level, Decimal("0"))
                if percent > 0:
                    bonus_amount = (Decimal(order.total) * percent).quantize(
                        Decimal("0.01")
                    )

                    await self.referral_bonus_crud.create(
                        referrer_id=parent_referral.id,
                        referral_id=referral.id,
                        order_id=order.id,
                        bonus_amount=bonus_amount,
                    )

                    referrer_user = await self.session.get(User, parent_referral.user_id)
                    if referrer_user:
                        referrer_user.bonus_balance += bonus_amount
                        self.session.add(referrer_user)
                        logger.info(
                            "Applied referral bonus and updated user balance",
                            extra={
                                "level": level,
                                "referrer_user_id": str(parent_referral.user_id),
                                "from_user_id": str(order.user_id),
                                "order_id": str(order.id),
                                "bonus_amount": str(bonus_amount),
                                "new_balance": str(referrer_user.bonus_balance)
                            },
                        )
                    else:
                        logger.error(f"Referrer user not found: {parent_referral.user_id}")


                current_referrer_id = parent_referral.referrer_id
                level += 1
        await self.session.commit()


    async def get_referral_details(
        self,
        *,
        user_id: UUID = None,
        referral_id: UUID = None,
    ) -> SReferral:
        referral = await self.referral_crud.get_or_create(
            user_id=user_id,
            referral_id=referral_id,
        )
        orders_count = await self.order_crud.get_current_month_orders_count(
            referral.user_id
        )
        referrals_count = await self.referral_crud.get_children_amount(referral.id)
        
        referral_bonus = await self.referral_bonus_crud.get_total_bonus_for_referrer(
            referral.id
        )
        withdrawable_balance = await self.referral_bonus_crud.get_available_balance(referral.id)
        
        total_balance = float(referral.user.bonus_balance)

        logger.info(
            "Get referral details",
            extra={
                "user_id": user_id,
                "referral_id": referral_id,
                "total_balance": total_balance,
                "withdrawable_balance": float(withdrawable_balance)
            },
        )
        return SReferral(
            id=referral.id,
            full_name=referral.user.full_name,
            current_month_orders=orders_count,
            total_balance=total_balance,
            withdrawable_balance=float(withdrawable_balance),
            referral_bonus=referral_bonus,
            referrals_count=referrals_count,
            invite_link=await self.get_invite_link(referral_id=referral.id),
            signed_conditions=referral.signed_conditions,
            signed_user_terms=referral.signed_user_terms,
            is_registered=referral.is_registered,
        )

    async def search_referrals_by_name(
        self,
        user_id: UUID,
        name: str,
        page: int = 1,
        page_size: int = 50,
    ) -> SReferralListPaginated:
        referral = await self.referral_crud.get_or_create(user_id=user_id)
        found_items, total = await self.referral_crud.search_children_by_name(
            referrer_id=referral.id,
            name_substr=name,
            page=page,
            page_size=page_size,
        )
        items = [
            SReferral(
                id=referral.id,
                full_name=item.referral.user.full_name,
                referrals_count=item.referral_count,
                referral_bonus=await self.referral_bonus_crud.get_total_bonus_for_referral(
                    item.referral.id
                ),
            )
            for item in found_items
        ]

        logger.info(
            "Search referrals by name", extra={"user_id": user_id, "search_name": name}
        )
        return SReferralListPaginated(
            items=items,
            total=total,
            pages=math.ceil(total / page_size),
            size=page_size,
        )

    async def get_referrer_children(
        self,
        *,
        user_id: UUID = None,
        referral_id: UUID = None,
        page: int = 1,
        page_size: int = 50,
    ) -> SReferralListPaginated:
        referrer = await self.referral_crud.get_or_create(
            user_id=user_id,
            referral_id=referral_id,
        )
        found_items, total = await self.referral_crud.get_children_with_counts(
            referrer_id=referrer.id,
            page=page,
            page_size=page_size,
        )
        items = [
            SReferral(
                id=item.referral.id,
                full_name=item.referral.user.full_name,
                referrals_count=item.referral_count,
                referral_bonus=await self.referral_bonus_crud.get_total_bonus_for_referral(
                    item.referral.id
                ),
            )
            for item in found_items
        ]

        logger.info("Get referrer children", extra={"user_id": user_id})
        return SReferralListPaginated(
            items=items,
            total=total,
            pages=math.ceil(total / page_size),
            size=page_size,
        )

    async def get_top_referrer_children(self, user_id: UUID) -> SReferralListPaginated:
        page_size = 10
        referrer = await self.referral_crud.get_or_create(user_id=user_id)
        total = await self.referral_crud.get_children_amount(referrer.id)
        top_children = await self.referral_crud.get_top_children_by_bonus(
            referrer.id,
            limit=page_size,
        )

        items = [
            SReferral(
                id=item.referral.id,
                full_name=item.referral.user.full_name,
                referral_bonus=await self.referral_bonus_crud.get_total_bonus_for_referral(
                    item.referral.id
                ),
                current_month_orders=item.current_month_orders,
            )
            for item in top_children
        ]

        logger.info("Get top referrer children", extra={"user_id": user_id})
        return SReferralListPaginated(
            items=items,
            total=total,
            pages=math.ceil(total / page_size),
            size=page_size,
        )

    async def sign_conditions(self, user_id: UUID) -> SReferral:
        await self.referral_crud.update_signed_flags(
            user_id,
            signed_conditions=True,
        )

        logger.info("Signed conditions (referral)", extra={"user_id": user_id})
        return await self.get_referral_details(user_id=user_id)

    async def sign_user_terms(self, user_id: UUID) -> SReferral:
        await self.referral_crud.update_signed_flags(
            user_id,
            signed_user_terms=True,
        )

        logger.info("Signed user terms (referral)", extra={"user_id": user_id})
        return await self.get_referral_details(user_id=user_id)

    async def create_payout_request(
        self,
        user_id: UUID,
        data: SReferralPayoutRequest,
    ) -> SReferralPayoutRequest:
        logger.info(
            "Creating a payout request",
            extra={"user_id": user_id, "data": data.model_dump()},
        )

        user = await self.referral_crud.get_or_create(user_id=user_id)

        if user.user.bonus_balance < data.amount:
            raise HTTPException(
                status_code=status.HTTP_417_EXPECTATION_FAILED,
                detail="The user balance is not sufficient to create a payout request",
            )

        payment_details = user.user.payment_details
        if not payment_details:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment details not set for the user",
            )

        new_request = await self.payout_request_crud.create(
            user_id=user_id,
            amount=data.amount,
            payment_details=payment_details,
        )

        user.user.bonus_balance -= Decimal(data.amount)
        await self.session.commit()

        return SReferralPayoutRequest.model_validate(new_request, from_attributes=True)

    async def get_payout_requests(
        self,
        *,
        request_id: Optional[UUID] = None,
        status_: Optional[ReferralPayoutStatus] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> SReferralPayoutRequestPaginated:
        dt_from = datetime.fromisoformat(from_date) if from_date else None
        dt_to = datetime.fromisoformat(to_date) if to_date else None

        items, total = await self.payout_request_crud.list_with_filters(
            request_id=request_id,
            status=status_,
            from_date=dt_from,
            to_date=dt_to,
            page=page,
            page_size=page_size,
        )

        out_items = []
        for req in items:
            out_items.append(
                SReferralPayoutRequest(
                    id=req.id,
                    bank_code=req.bank_code,
                    account_number=req.account_number,
                    amount=float(req.amount),
                    status=req.status,
                    referrer_id=req.referrer_id,
                    referrer=SReferrer(
                        id=req.referrer.id,
                        full_name=req.referrer.user.full_name,
                    ),
                    created_at=req.created_at,
                )
            )

        return SReferralPayoutRequestPaginated(
            items=out_items,
            total=total,
            pages=math.ceil(total / page_size),
            size=page_size,
        )

    async def approve_payout_request(self, request_id: UUID) -> SReferralPayoutRequest:
        logger.info(
            "Approving payout request",
            extra={"request_id": request_id},
        )
        request = await self.payout_request_crud.get_by_id(request_id)
        referrer_balance = await self.referral_bonus_crud.get_available_balance(
            request.referrer.id
        )

        if referrer_balance < request.amount:
            raise HTTPException(
                status_code=status.HTTP_417_EXPECTATION_FAILED,
                detail="The user balance is not sufficient to approve the payout request",
            )

        new_request = await self.payout_request_crud.update_status(
            request_id,
            ReferralPayoutStatus.APPROVED,
        )
        data = new_request.__dict__
        data["referrer"] = SReferrer(
            id=new_request.id,
            full_name=new_request.referrer.user.full_name,
        )

        return SReferralPayoutRequest.model_validate(data)

    async def reject_payout_request(self, request_id: UUID) -> SReferralPayoutRequest:
        logger.info(
            "Rejecting payout request",
            extra={"request_id": request_id},
        )
        return SReferralPayoutRequest.model_validate(
            await self.payout_request_crud.update_status(
                request_id,
                ReferralPayoutStatus.REJECTED,
            )
        )
