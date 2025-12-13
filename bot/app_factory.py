import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .handlers.start import router as start_router
from .handlers.profile import router as profile_router
from .handlers.task.catalog import router as tasks_router
from .handlers.task.submission import router as submission_router
from .handlers.admin.panel import router as admin_router


def build_dispatcher(bot_token: str) -> tuple[Bot, Dispatcher]:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(tasks_router)
    dp.include_router(submission_router)
    dp.include_router(admin_router)
    return bot, dp
