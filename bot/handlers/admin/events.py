# bot/handlers/admin/events.py

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command

from ...filters.roles import IsAdmin
from ...services.events import create_event, list_upcoming_events
from ...keyboards.common import admin_panel_kb, calendar_root_kb

from datetime import datetime

router = Router(name="admin_events")


class EventCreate(StatesGroup):
    waiting_title = State()
    waiting_date = State()
    waiting_time = State()
    waiting_description = State()


# вход в раздел "События" из главной админки
@router.callback_query(IsAdmin(), F.data == "admin:events")
async def admin_events_root(cb: CallbackQuery):
    await cb.message.edit_text(
        "📅 <b>Управление событиями</b>\n"
        "Здесь можно добавить событие в календарь или посмотреть список ближайших.",
        reply_markup=calendar_root_kb(),
    )
    await cb.answer()


# показать список ближайших событий
@router.callback_query(IsAdmin(), F.data == "admin:events:list")
async def admin_events_list(cb: CallbackQuery):
    events = list_upcoming_events(limit=20)

    if not events:
        await cb.message.edit_text(
            "Пока нет запланированных событий.",
            reply_markup=calendar_root_kb(),
        )
        await cb.answer()
        return

    lines: list[str] = ["📅 <b>Ближайшие события</b>:\n"]
    for ev in events:
        dt = ev.starts_at
        dt_str = dt.strftime("%Y-%m-%d %H:%M")
        desc = ev.description or "—"
        lines.append(f"• <b>{ev.title}</b>\n  🕒 {dt_str}\n  📝 {desc}\n  ID: {ev.id}")

    await cb.message.edit_text(
        "\n\n".join(lines),
        reply_markup=calendar_root_kb(),
    )
    await cb.answer()


# старт создания события
@router.callback_query(IsAdmin(), F.data == "admin:events:add")
async def admin_event_add_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(EventCreate.waiting_title)
    await cb.message.edit_text(
        "📝 <b>Новое событие</b>\n"
        "Отправь название события одним сообщением.\n\n"
        "Отмена: /cancel",
    )
    await cb.answer()


@router.message(EventCreate.waiting_title)
async def admin_event_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text.strip())
    await state.set_state(EventCreate.waiting_date)
    await msg.answer(
        "📅 Введи дату события в формате <code>YYYY-MM-DD</code>\n"
        "Например: <code>2025-12-10</code>\n\n"
        "Отмена: /cancel"
    )


@router.message(EventCreate.waiting_time)
async def admin_event_time(msg: Message, state: FSMContext):
    time_raw = msg.text.strip()
    data = await state.get_data()

    title = data["title"]
    description = data.get("description")
    date_raw = data["date"]   # вот тут уже ОК — мы её сохранили в предыдущем шаге

    # валидируем и собираем datetime
    try:
        dt = datetime.strptime(f"{date_raw} {time_raw}", "%Y-%m-%d %H:%M")
    except ValueError:
        await msg.answer(
            "❌ Неверный формат времени.\n"
            "Формат: <b>ЧЧ:ММ</b>, например: <code>18:30</code>"
        )
        return

    # создаём событие
    create_event(
        title=title,
        description=description,
        event_dt=dt,          # тут подставь те аргументы, которые ждёт твой create_event
        creator_tg_id=msg.from_user.id,
    )

    await state.clear()
    await msg.answer("✅ Событие добавлено в календарь!", reply_markup=admin_panel_kb())


@router.message(EventCreate.waiting_time)
async def admin_event_time(msg: Message, state: FSMContext):
    text = msg.text.strip()
    try:
        t = datetime.strptime(text, "%H:%M").time()
    except ValueError:
        await msg.answer("❌ Неверный формат времени. Пример: <code>19:30</code>")
        return

    await state.update_data(time=text)
    await state.set_state(EventCreate.waiting_description)
    await msg.answer(
        "✏️ Теперь отправь описание события (можно в несколько строк).\n"
        "Если описания не нужно — отправь дефис <code>-</code>."
    )


@router.message(EventCreate.waiting_description)
async def admin_event_description(msg: Message, state: FSMContext):
    data = await state.get_data()
    title = data["title"]
    date_str = data["date"]
    time_str = data["time"]

    description = None if msg.text.strip() == "-" else msg.text.strip()

    # собираем datetime
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")

    event_id = create_event(title=title, description=description, created_at=dt)
    await state.clear()

    await msg.answer(
        f"✅ Событие создано!\n\n"
        f"<b>{title}</b>\n"
        f"🕒 {dt.strftime('%Y-%m-%d %H:%M')}\n"
        f"ID: <code>{event_id}</code>",
        reply_markup=admin_panel_kb(),
    )


@router.message(Command("cancel"))
async def admin_event_cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Отменено.", reply_markup=admin_panel_kb())