# diagnostic.py
import asyncio
import os
import sys

from aiogram import Bot
from aiogram.types import BufferedInputFile


async def test_send_file():
    # Использование токена из окружения
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)

    # Тестовый чат ID
    chat_id = 463810412  # Ваш Telegram ID из логов

    # Создаем тестовый файл
    content = b"Hello, this is a test file from diagnostic script"
    filename = "test.txt"

    print(f"Creating bot with token {token[:5]}...")
    bot = Bot(token=token)

    try:
        print("Testing bot.get_me()...")
        me = await bot.get_me()
        print(f"Bot info: {me.username} (ID: {me.id})")

        print(f"Preparing to send file to chat {chat_id}...")
        input_file = BufferedInputFile(
            file=content,
            filename=filename
        )

        print("Sending document...")
        await bot.send_document(
            chat_id=chat_id,
            document=input_file,
            caption="Test file from diagnostic script"
        )
        print("Document sent successfully!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.session.close()
        print("Session closed")


if __name__ == "__main__":
    asyncio.run(test_send_file())
