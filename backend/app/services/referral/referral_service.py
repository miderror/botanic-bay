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
from app.crud.payout_request import ReferralPayoutRequestCRUD
from app.crud.referral import ReferralCRUD
from app.crud.referral_bonus import ReferralBonusCRUD
from app.enums.referral import ReferralPayoutStatus
from app.models import Order
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
        payout_request_crud: ReferralPayoutRequestCRUD,
        session: AsyncSession,
    ):
        self.bot_manager = bot_manager
        self.referral_crud = referral_crud
        self.referral_bonus_crud = referral_bonus_crud
        self.order_crud = order_crud
        self.payout_request_crud = payout_request_crud
        self.session = session

    async def get_invite_link(
        self,
        *,
        user_id: Optional[UUID] = None,
        referral_id: Optional[UUID] = None,
    ) -> str:
        if referral_id is None and user_id is None:
            raise ValueError(
                "Either user_id or referral_id " "must be set to get an invite link!"
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
        if order.status != OrderStatus.DELIVERED:
            return

        referral = await self.referral_crud.get(user_id=order.user_id)
        if not referral:
            return

        current = referral
        level = 1

        async with self.session.begin():
            while current.referrer_id and level <= settings.REFERRAL_MAX_LEVEL:
                parent = await self.referral_crud.get(referral_id=current.referrer_id)
                if not parent:
                    break

                percent = settings.REFERRAL_LEVELS.get(level, 0)
                if percent:
                    bonus_amount = (order.total * Decimal(percent)).quantize(
                        Decimal("0.01")
                    )

                    await self.referral_bonus_crud.create(
                        referrer_id=parent.id,
                        referral_id=referral.id,
                        order_id=order.id,
                        bonus_amount=bonus_amount,
                    )

                    logger.info(
                        "Applied referral bonus",
                        extra={
                            "level": level,
                            "referrer_referral_id": parent.id,
                            "referrer_user_id": parent.user_id,
                            "original_referral_id": referral.id,
                            "order_id": order.id,
                            "bonus_amount": str(bonus_amount),
                        },
                    )

                current = parent
                level += 1

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
        referrals_count = await self.referral_crud.get_children_amount(referral_id)
        referral_bonus = await self.referral_bonus_crud.get_total_bonus_for_referrer(
            referral.id
        )
        balance = await self.referral_bonus_crud.get_available_balance(referral.id)

        logger.info(
            "Get referral details",
            extra={
                "user_id": user_id,
                "referral_id": referral_id,
            },
        )
        return SReferral(
            id=referral.id,
            full_name=referral.user.full_name,
            current_month_orders=orders_count,
            balance=float(balance),
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
        referrer = await self.referral_crud.get_or_create(user_id=user_id)
        balance = await self.referral_bonus_crud.get_available_balance(referrer.id)

        if not referrer.is_registered:
            raise HTTPException(
                status_code=status.HTTP_417_EXPECTATION_FAILED,
                detail="User is not registered in referral program",
            )
        if float(balance) < data.amount:
            raise HTTPException(
                status_code=status.HTTP_417_EXPECTATION_FAILED,
                detail="The user balance is not sufficient to create a payout request",
            )

        return SReferralPayoutRequest.model_validate(
            await self.payout_request_crud.create(
                referrer_id=referrer.id,
                bank_code=data.bank_code,
                account_number=data.account_number,
                amount=data.amount,
            )
        )

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
