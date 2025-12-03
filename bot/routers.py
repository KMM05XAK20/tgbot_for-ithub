from aiogram import Router

root_router = Router(name="root")


from .handlers import start, menu, profile, rating
from .handlers.task import catalog, submission
from .handlers import mentorship, calendar, help
from .handlers.admin import panel, tasks, grant, broadcast
from .handlers import debug

# Включаем под-роутеры
root_router.include_routers(
    start.router,
    menu.router,
    tasks.router,
    broadcast.router,
    panel.router,
    grant.router,
    profile.router,
    rating.router,
    catalog.router,
    submission.router,
    mentorship.router,
    calendar.router,
    help.router, 
    debug.router,
)