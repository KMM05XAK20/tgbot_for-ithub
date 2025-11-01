from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from ...filters.roles import IsAdmin
from ...keyboards.common import admin_root_kb, admin_pending_kb, admin_assignment_kb
from ...services.tasks import (
    list_pending_submissions, get_assignment_full,
    approve_assignment, reject_assignment
)

router = Router()

# /whoami ты уже сделал в start.py — ок

# Вход в админку (команда с фильтром IsAdmin)
@router.message(Command("admin"), IsAdmin())
async def admin_entry(msg: Message):
    await msg.answer("🛠 <b>Админ-панель</b>\nВыберите раздел:", reply_markup=admin_root_kb())

# Список «на проверке»
@router.callback_query(F.data.startswith("admin:pending:"), IsAdmin())
async def admin_pending(cb: CallbackQuery):
    page = int(cb.data.split(":")[-1])
    rows = list_pending_submissions(page=page, per_page=10)
    if not rows:
        await cb.message.edit_text("🕒 На проверке пусто.", reply_markup=admin_pending_kb(page))
        return await cb.answer()

    lines = []
    for aid, title, tg_id, username, submitted_at in rows:
        user = f"@{username}" if username else str(tg_id)
        when = submitted_at.strftime("%Y-%m-%d %H:%M") if submitted_at else "—"
        lines.append(f"• <a href='tg://user?id={tg_id}'>[{user}]</a> — <b>{title}</b> — id:{aid} — {when}")

    text = "🕒 <b>На проверке</b>\n" + "\n".join(lines) + "\n\nОткрой карточку: напиши в чат <code>admin:view:&lt;id&gt;</code>"
    await cb.message.edit_text(text, reply_markup=admin_pending_kb(page), disable_web_page_preview=True)
    await cb.answer()

# Просмотр карточки по текстовой команде: admin:view:<id>
@router.message(F.text.startswith("admin:view:"), IsAdmin())
async def admin_view_by_text(msg: Message):
    try:
        aid = int(msg.text.split(":")[-1])
    except Exception:
        return await msg.answer("Формат: admin:view:<assignment_id>")
    await show_assignment_card(msg, aid)

# Просмотр карточки (если позже сделаешь inline-кнопку admin:view:<id>)
@router.callback_query(F.data.startswith("admin:view:"), IsAdmin())
async def admin_view_cb(cb: CallbackQuery):
    aid = int(cb.data.split(":")[-1])
    await show_assignment_card(cb.message, aid)
    await cb.answer()

async def show_assignment_card(target: Message, assignment_id: int):
    a = get_assignment_full(assignment_id)
    if not a:
        return await target.answer("Запись не найдена.")
    t, u = a.task, a.user
    user = f"@{u.username}" if u.username else str(u.tg_id)
    sub = a.submission_text or "(текст не прислан)"
    file_note = "да" if a.submission_file_id else "нет"
    text = (
        f"📄 <b>Заявка #{a.id}</b>\n"
        f"👤 Пользователь: <a href='tg://user?id={u.tg_id}'>{user}</a>\n"
        f"📌 Задание: <b>{t.title}</b>\n"
        f"🪙 Награда: +{t.reward_coins} coins\n"
        f"⏱ Дедлайн: {a.due_at.strftime('%Y-%m-%d %H:%M') if a.due_at else '—'}\n"
        f"📥 Текст: {sub}\n"
        f"🖼️ Фото приложено: {file_note}\n"
        f"Статус: <b>{a.status}</b>"
    )
    await target.answer(text, reply_markup=admin_assignment_kb(a.id), disable_web_page_preview=True)

# Approve
@router.callback_query(F.data.startswith("admin:approve:"), IsAdmin())
async def admin_approve(cb: CallbackQuery):
    aid = int(cb.data.split(":")[-1])
    if not approve_assignment(aid):
        await cb.answer("Не удалось подтвердить.", show_alert=True)
        return
    await cb.answer("Подтверждено, монеты начислены.", show_alert=True)

    # уведомим пользователя
    a = get_assignment_full(aid)
    try:
        await cb.bot.send_message(
            a.user.tg_id,
            f"✅ Ваше задание <b>{a.task.title}</b> проверено. Начислено <b>+{a.task.reward_coins}</b> coins!"
        )
    except Exception:
        pass

# Reject
@router.callback_query(F.data.startswith("admin:reject:"), IsAdmin())
async def admin_reject(cb: CallbackQuery):
    aid = int(cb.data.split(":")[-1])
    if not reject_assignment(aid):
        await cb.answer("Не удалось отклонить.", show_alert=True)
        return
    await cb.answer("Отклонено.", show_alert=True)

    a = get_assignment_full(aid)
    try:
        await cb.bot.send_message(
            a.user.tg_id,
            f"❌ Ваше задание <b>{a.task.title}</b> отклонено.\nПопробуйте ещё раз — уточните детали и пришлите новый вариант."
        )
    except Exception:
        pass
