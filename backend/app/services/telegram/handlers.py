import json
from urllib.parse import urlencode

from aiogram import Router, types
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.utils.payload import decode_payload

from app.core.logger import logger
from app.core.settings import settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    """
    Универсальный обработчик команды /start.
    Работает и с deeplink (реферальной ссылкой), и без нее.
    """
    web_app_url = settings.FRONTEND_URL

    if command.args:
        try:
            payload = json.loads(decode_payload(command.args))
            query = urlencode(payload)
            web_app_url = f"{settings.FRONTEND_URL}?{query}"
            logger.info("User started bot with deeplink", extra={"payload": payload})
        except Exception as e:
            logger.error(
                "Failed to decode deeplink payload",
                extra={"args": command.args, "error": str(e)},
            )

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🏪 Открыть магазин", web_app=types.WebAppInfo(url=web_app_url)
                )
            ]
        ]
    )

    await message.answer(
        "👋 Добро пожаловать в магазин БАДов!\n\n"
        "Нажмите кнопку ниже, чтобы открыть каталог товаров.",
        reply_markup=keyboard,
    )

    logger.info(
        "User started the bot",
        extra={"user_id": message.from_user.id, "username": message.from_user.username},
    )


@router.message(Command("shop"))
async def cmd_shop(message: types.Message):
    """
    Обработчик команды /shop
    Отправляет inline кнопку для открытия WebApp
    """
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🏪 Открыть магазин",
                    web_app=types.WebAppInfo(url=settings.FRONTEND_URL),
                )
            ]
        ]
    )

    await message.answer(
        "Нажмите кнопку ниже, чтобы открыть каталог:", reply_markup=keyboard
    )
