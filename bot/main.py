import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .routers import root_router
from .config import get_settings


logging.basicConfig(level=logging.DEBUG)


async def main():
    settings = get_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(root_router)


    if settings.use_webhook:
        print("Webhook mode включен — пропуск опроса.")
        return
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    #await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())