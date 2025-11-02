import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import get_settings
from .handlers.start import router as start_router
from .handlers.profile import router as profile_router
from .handlers.task.catalog import router as task_router
from .handlers.task.submission import router as submission_router
from .handlers.admin.panel import router as admin_router
from .handlers.rating import router as rating_router
from .handlers.menu import router as menu_router

logging.basicConfig(level=logging.INFO)

async def main():
    settings = get_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(task_router)
    dp.include_router(submission_router)
    dp.include_router(admin_router)
    dp.include_router(rating_router)
    dp.include_router(menu_router)

    if settings.use_webhook:
        print("Webhook mode включен — пропуск опроса.")
        return
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

    #await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())
