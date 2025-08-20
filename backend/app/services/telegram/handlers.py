# backend/app/services/telegram/handlers.py
import json
from urllib.parse import urlencode

from aiogram import Router, types
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.utils.payload import decode_payload

from app.core.logger import logger
from app.core.settings import settings

router = Router()


@router.message(CommandStart(deep_link=True))
async def cmd_start(message: types.Message, command: CommandObject):
    """
    Обработчик команды /start
    Отправляет приветственное сообщение и кнопку для открытия WebApp
    """
    args = command.args
    payload = json.loads(decode_payload(args))

    query = urlencode(payload)
    web_app_url = f"{settings.FRONTEND_URL}?{query}"

    await message.answer(web_app_url)

    # Создаем клавиатуру с кнопкой для открытия WebApp
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🏪 Открыть магазин", web_app=types.WebAppInfo(url=web_app_url)
                )
            ]
        ]
    )

    # Отправляем приветственное сообщение
    await message.answer(
        "👋 Добро пожаловать в магазин БАДов!\n\n"
        "Нажмите кнопку ниже, чтобы открыть каталог товаров.",
        reply_markup=keyboard,
    )

    logger.info(
        "User started the bot",
        extra={"user_id": message.from_user.id, "username": message.from_user.username},
    )


# Также можно добавить inline кнопку для открытия WebApp
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
