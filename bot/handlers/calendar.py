from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from ..services.calendar import get_upcoming_events, get_all_events, list_upcomming_events, list_all_events
from ..keyboards.common import profile_kb
from ..keyboards.common import calendar_root_kb
from ..keyboards.common import main_menu_kb

router = Router(name="calendar")


@router.callback_query(F.data == "menu:open:calendar")
async def open_calendar(cb: CallbackQuery):
    events = get_upcoming_events(cb.from_user.id, limit=5)
    if not events:
        text = "📅 <b>Календарь</b>\nПока нет ближайших событий."
    else:
        rows = []
        for e in events:
            dt = e.event_date.strftime("%Y-%m-%d %H:%M")
            rows.append(f"• {e.title} — {dt}")
        text = "📅 <b>Ближайшие события</b>\n\n" + "\n".join(rows)

    await cb.message.edit_text(text, reply_markup=calendar_root_kb())
    await cb.answer()

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
@router.callback_query(F.data == "mentor:choose") # calendar:all // mentor:choose" 
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


def _render_events(events) -> str:

    if not events:
        return "Пока нет ближайших событий 🙈"
    
    lines: list[str] = ["🗓 <b>Ближайшие события</b>:\n"]
    
    for ev in events:

        title = getattr(ev, "title", "Без названия")
        desc  = (getattr(ev, "description", "") or "").strip()
        dt    = getattr(ev, "start_at", None)\
        
        if dt is None:
            dt_str = dt.strftime("%d.%m %H:%M")
        else:
            dt_str = "Время не указано"

        if desc:
            short_desc = (desc[:20] + "...") if len(desc) > 120 else desc
            desc_part = f"\n {short_desc}"
        else:
            desc_part = ""

        lines.append( 
            f"• <b>{title}</b>\n"
            f"  🕒 {dt_str}"
            f"{desc_part}"
            )
    return "\n\n".join(lines)

@router.callback_query(F.data == "menu:open:calendar")
async def open_calendar_root(cb: CallbackQuery):

    events =  list_upcomming_events(limit=5)
    text = _render_events(events)

    await cb.message.edit_text(
        text,
        reply_markup=calendar_root_kb(),
        parse_mode=ParseMode.HTML(),
    )
    await cb.answer()

@router.callback_query(F.data =="calendar:all")
async def open_caledar_all(cb: CallbackQuery):

    events = list_all_events(limit=50)

    if not events:
        text = "Пока нет запланированных событий 🙈"
    else:
        text = _render_events(events).replace(
        "🗓 <b>Ближайшие события</b>:", "📅 <b>Весь календарь</b>:"
    )

    await cb.message.answer(
        text,
        reply_markup=calendar_root_kb(),
        parse_mode=ParseMode.HTML,
    )
    await cb.answer()

@router.callback_query(F.data == "menu:open:main")
async def back_to_main_menu(cb: CallbackQuery):
    text = "Вы вернулись в главное меню."
    await cb.message.edit_text(text, reply_markup=main_menu_kb())  # Главное меню
    await cb.answer()