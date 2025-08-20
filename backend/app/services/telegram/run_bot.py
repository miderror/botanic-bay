# backend/app/services/telegram/run_bot.py
import asyncio

from app.core.logger import logger
from app.services.telegram.bot_manager import TelegramBotManager


async def main():
    bot_manager = TelegramBotManager()
    try:
        logger.info("Starting Telegram bot")
        await bot_manager.start()
    except Exception as e:
        logger.error(f"Error while running bot: {e}", exc_info=True)
        raise
    finally:
        if bot_manager.bot:
            await bot_manager.stop()


if __name__ == "__main__":
    asyncio.run(main())
