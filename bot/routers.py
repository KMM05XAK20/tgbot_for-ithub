from aiogram import Router

root_router = Router(name="root")

# обычные хендлеры
from .handlers import start, menu, profile, rating, mentorship, calendar, help, debug

# хендлеры заданий (каталог + сдача)
from .handlers.task import catalog, submission

# админские хендлеры
from .handlers.admin import panel, tasks, grant, broadcast, events, stats


root_router.include_routers(
    # пользователи
    start.router,
    menu.router,
    profile.router,
    rating.router,
    mentorship.router,
    calendar.router,
    help.router,
    debug.router,

    # задания (каталог/сдача)
    catalog.router,
    submission.router,

    # админка
    panel.router,
    tasks.router,
    grant.router,
    broadcast.router,
    stats.router,
    events.router,
)
