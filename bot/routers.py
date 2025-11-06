from aiogram import Router

root_router = Router(name="root")


from .handlers import start, menu, profile, rating
from .handlers.task import catalog, submission
from .handlers.admin import panel
from .handlers import mentorship, calendar
from .handlers import debug

# Включаем под-роутеры
root_router.include_routers(
    start.router,
    menu.router,
    profile.router,
    rating.router,
    catalog.router,
    submission.router,
    panel.router,
    mentorship.router,
    calendar.router,
    debug.router
)