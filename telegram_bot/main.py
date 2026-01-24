from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from telegram_bot.handlers.booking import router as booking_router
from telegram_bot.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_storage():
    try:
        redis = Redis.from_url(settings.redis_url)
        await redis.ping()
        return RedisStorage(redis)
    except Exception:  # noqa: BLE001
        logger.warning("Redis unavailable, using MemoryStorage")
        return MemoryStorage()


async def main() -> None:
    if not settings.telegram_bot_token:
        logger.info("TELEGRAM_BOT_TOKEN missing, bot disabled")
        await asyncio.Event().wait()
        return

    bot = Bot(token=settings.telegram_bot_token)
    if not settings.telegram_bot_username:
        try:
            me = await bot.get_me()
            settings.telegram_bot_username = me.username
        except Exception:  # noqa: BLE001
            logger.warning("Failed to fetch bot username; set TELEGRAM_BOT_USERNAME")

    storage = await create_storage()
    dp = Dispatcher(storage=storage)
    dp.include_router(booking_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
