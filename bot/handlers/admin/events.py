# bot/handlers/admin/events.py
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from ...states.events import AdminEventForm
from ...keyboards.common import admin_events_kb
from ...services.events import create_event, list_upcoming_events

router = Router(name="admin_events")


# === Корень "События" в админке ===

@router.callback_query(F.data == "admin:events")
async def admin_events_root(cb: CallbackQuery):
    events = list_upcoming_events(limit=10)
    if not events:
        text = "📅 <b>События</b>\n\nПока событий нет.\nНажми «➕ Добавить событие»."
    else:
        lines = ["📅 <b>События</b>"]
        for e in events:
            dt_str = e.event_date.strftime("%Y-%m-%d %H:%M")
            lines.append(f"• <b>{e.title}</b>\n  🕒 {dt_str}")
        text = "\n\n".join(lines)

    await cb.message.edit_text(text, reply_markup=admin_events_kb())
    await cb.answer()


# === Старт добавления события ===

@router.callback_query(F.data == "admin:events:add")
async def admin_events_add_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("📝 Введи название события:")
    await state.set_state(AdminEventForm.waiting_title)
    await cb.answer()


# === Шаг 1: название ===

@router.message(AdminEventForm.waiting_title)
async def admin_event_title(msg: Message, state: FSMContext):
    title = msg.text.strip()
    if not title:
        await msg.answer("❌ Название не может быть пустым. Введи ещё раз.")
        return

    await state.update_data(title=title)
    await msg.answer(
        "✏ Введи описание события (или отправь <code>-</code>, чтобы пропустить):"
    )
    await state.set_state(AdminEventForm.waiting_description)


# === Шаг 2: описание ===

@router.message(AdminEventForm.waiting_description)
async def admin_event_description(msg: Message, state: FSMContext):
    raw = msg.text.strip()
    description = None if raw == "-" else raw

    await state.update_data(description=description)
    await msg.answer(
        "📅 Введи дату события в формате <b>ГГГГ-ММ-ДД</b>\n"
        "Например: <code>2025-12-24</code>"
    )
    await state.set_state(AdminEventForm.waiting_date)


# === Шаг 3: дата ===

@router.message(AdminEventForm.waiting_date)
async def admin_event_date(msg: Message, state: FSMContext):
    date_raw = msg.text.strip()

    # ✅ Проверяем формат ГГГГ-ММ-ДД
    try:
        datetime.strptime(date_raw, "%Y-%m-%d")
    except ValueError:
        await msg.answer(
            "❌ Неверный формат даты.\n"
            "Формат: <b>ГГГГ-ММ-ДД</b>\n"
            "Например: <code>2025-12-24</code>"
        )
        return

    await state.update_data(date=date_raw)

    await msg.answer(
        f"🕒 Введи время для события на {date_raw}\n"
        f"Формат: <b>ЧЧ:ММ</b>, например: <code>18:30</code>"
    )
    await state.set_state(AdminEventForm.waiting_time)


# === Шаг 4: время + создание ===

@router.message(AdminEventForm.waiting_time)
async def admin_event_time(msg: Message, state: FSMContext):
    time_raw = msg.text.strip()
    data = await state.get_data()

    title = data["title"]
    description = data.get("description")
    date_raw = data["date"]  # мы её сохранили на предыдущем шаге

    # валидируем дату+время
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
        event_dt=dt,
        creator_tg_id=msg.from_user.id,
    )

    await state.clear()
    await msg.answer("✅ Событие добавлено в календарь!", reply_markup=admin_events_kb())
