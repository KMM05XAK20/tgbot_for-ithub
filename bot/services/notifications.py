from datetime import datetime, timedelta
from ..services.calendar import get_upcoming_events
from ..services.users import get_user
from aiogram import Bot
from aiogram.types import ParseMode

async def send_event_reminders(bot: Bot):
    now = datetime.utcnow()
    upcoming_events = get_upcoming_events(user_id=None, limit=100)  # Получаем ближайшие события для всех пользователей

    for event in upcoming_events:
        reminder_time = event.event_date - timedelta(hours=1)  # Напоминание за 1 час до события
        if now >= reminder_time and now <= event.event_date:
            user = get_user(event.user_id)
            if user:
                message = (
                    f"⏰ Напоминание о событии: {event.title}\n"
                    f"Описание: {event.description}\n"
                    f"Дата и время: {event.event_date.strftime('%Y-%m-%d %H:%M')}"
                )
                await bot.send_message(user.telegram_id, message, parse_mode=ParseMode.HTML)
