import asyncio

from app.core.db import async_session
from app.core.init_db import init_roles
from app.core.logger import logger


async def init():
    logger.info("Starting database initialization...")
    async with async_session() as session:
        await init_roles(session)
        logger.info("Database initialization completed successfully!")


def main():
    try:
        asyncio.run(init())
    except Exception as e:
        logger.error(f"Error during database initialization: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
