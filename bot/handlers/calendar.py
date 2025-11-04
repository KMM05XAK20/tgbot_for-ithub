from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from ..services.calendar import get_upcoming_events, get_all_events
from ..keyboards.common import profile_kb

router = Router()

# Показ ближайших событий
@router.message(Command("calendar"))
async def show_upcoming_events(msg: Message):
    user_id = msg.from_user.id
    events = get_upcoming_events(user_id)

    if not events:
        await msg.answer("У вас нет предстоящих событий.")
        return

    text = "📅 <b>Ближайшие события:</b>\n\n"
    for event in events:
        event_date = event.event_date.strftime("%Y-%m-%d %H:%M")
        text += f"{event.title} — {event_date}\n"

    await msg.answer(text, reply_markup=profile_kb())

# Показ всех событий
@router.callback_query(F.data == "calendar:all")
async def show_all_events(cb: CallbackQuery):
    user_id = cb.from_user.id
    events = get_all_events(user_id)

    if not events:
        await cb.message.edit_text("У вас нет событий.")
        return

    text = "📅 <b>Все события:</b>\n\n"
    for event in events:
        event_date = event.event_date.strftime("%Y-%m-%d %H:%M")
        text += f"{event.title} — {event_date}\n"

    await cb.message.edit_text(text, reply_markup=profile_kb())
    await cb.answer()

