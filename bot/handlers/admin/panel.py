from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from ...filters.roles import IsAdmin
from ...storage.db import SessionLocal
from ...storage.models import User as UserModel
from ...keyboards.common import (
    admin_panel_kb,
    admin_pending_kb,
    admin_assignment_kb,
    admin_mentors_root_kb,
    mentor_role_kb,
)
from ...services.users import (
    find_user,
    get_or_create_user,
    set_user_role,
    set_admin_status,
    get_recent_users,
)
from ...services.mentorship import get_mentor_list
from ...states.mentorship import AdminMentorAdd, AdminMentorRemove
from ...services.levels import level_by_coins
from ...services.badges import newly_unlocked_badge
from ...services.tasks import (
    list_pending_submissions,
    get_assignment_full,
    approve_assignment,
    reject_assignment,
)
from ...services.calendar import create_event
from ...config import get_settings

router = Router(name="admin_panel")

# /whoami в start.py — ок


# Вход в админку (команда с фильтром IsAdmin)
@router.message(Command("admin"), IsAdmin())
async def admin_entry(msg: Message):
    await msg.answer(
        "🛠 <b>Админ-панель</b>\nВыберите раздел:", reply_markup=admin_panel_kb()
    )


# Список «на проверке»
@router.callback_query(F.data.startswith("admin:pending:"), IsAdmin())
async def admin_pending(cb: CallbackQuery):
    page = int(cb.data.split(":")[-1])
    rows = list_pending_submissions(page=page, per_page=10)
    if not rows:
        await cb.message.edit_text(
            "🕒 На проверке пусто.", reply_markup=admin_pending_kb(page)
        )
        return await cb.answer()

    lines = []
    for aid, title, tg_id, username, submitted_at in rows:
        user = f"@{username}" if username else str(tg_id)
        when = submitted_at.strftime("%Y-%m-%d %H:%M") if submitted_at else "—"
        lines.append(
            f"• <a href='tg://user?id={tg_id}'>[{user}]</a> — <b>{title}</b> — id:{aid} — {when}"
        )

    text = (
        "🕒 <b>На проверке</b>\n"
        + "\n".join(lines)
        + "\n\nОткрой карточку: напиши в чат <code>admin:view:&lt;id&gt;</code>"
    )
    await cb.message.edit_text(
        text, reply_markup=admin_pending_kb(page), disable_web_page_preview=True
    )
    await cb.answer()


@router.message(IsAdmin(), Command("add_admin"))
async def add_admin(msg: Message):
    if not msg.reply_to_message:
        return await msg.answer("Сделай /add_admin ответом на сообщение пользывателя.")

    target = msg.reply_to_message.from_user
    tg_id = target.id

    with SessionLocal() as s:
        user = s.query(UserModel).filter_by(tg_id=tg_id).first()
        if not user:
            user = UserModel(tg_id=tg_id, username=target.username)
            s.add(user)
        user.is_admin = True
        s.commit()

    await msg.answer(
        f"✅ Пользователь @{target.username or tg_id} теперь администратор."
    )


@router.message(IsAdmin(), Command("del_admin"))
async def del_admin(msg: Message):
    if not msg.reply_to_message:
        return await msg.answer("Сделай /del_admin ответом на сообщение пользователя.")

    target = msg.reply_to_message.from_user
    tg_id = target.id

    from ...config import get_settings

    settings = get_settings()
    super_ids = set(settings.admin_ids or [])

    # не даём снести супер-админа из .env
    if tg_id in super_ids:
        return await msg.answer("Нельзя снять супер-админа, он прописан в .env")

    with SessionLocal() as s:
        user = s.query(UserModel).filter_by(tg_id=tg_id).first()
        if not user or not user.is_admin:
            return await msg.answer("Этот пользователь и так не админ.")
        user.is_admin = False
        s.commit()

    await msg.answer(f"🚫 Пользователь @{target.username or tg_id} больше не админ.")


@router.callback_query(F.data.startswith("admin:grant:"))
async def admin_grant(cb: CallbackQuery):
    settings = get_settings()

    # Проверяем, что вызывающий — супер-админ
    if cb.from_user.id not in settings.admin_ids:
        await cb.answer("❌ Недостаточно прав", show_alert=True)
        return

    target_id = int(cb.data.split(":")[2])

    # Обновляем базу
    set_admin_status(target_id, True)

    await cb.answer("Пользователь теперь админ!", show_alert=True)
    await cb.message.edit_text("Админка выдана.")


# Просмотр карточки по текстовой команде: admin:view:<id>
@router.message(F.text.startswith("admin:view:"), IsAdmin())
async def admin_view_by_text(msg: Message):
    try:
        aid = int(msg.text.split(":")[-1])
    except Exception:
        return await msg.answer("Формат: admin:view:<assignment_id>")
    await show_assignment_card(msg, aid)


@router.message(Command("create_event"))
async def create_event_cmd(msg: types.Message):
    # Пример создания события через команду
    title = "Пример события"
    description = "Описание события"
    event_date = datetime.utcnow() + timedelta(days=2)  # через 2 дня
    create_event(
        user_id=msg.from_user.id,
        title=title,
        description=description,
        event_date=event_date,
    )
    await msg.answer(f"Событие '{title}' успешно создано!")


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
    await target.answer(
        text, reply_markup=admin_assignment_kb(a.id), disable_web_page_preview=True
    )


# Approve
@router.callback_query(F.data.startswith("admin:approve:"), IsAdmin())
async def admin_approve(cb: CallbackQuery):
    aid = int(cb.data.split(":")[-1])

    # получим данные ДО апрува (для сравнения уровней)
    a_before = get_assignment_full(aid)
    if not a_before:
        await cb.answer("Не найдена заявка.", show_alert=True)
        return
    user_before = a_before.user
    coins_before = user_before.coins or 0
    lvl_before = level_by_coins(coins_before).level

    if not approve_assignment(aid):  # здесь начисляются coins пользователю
        await cb.answer("Не удалось подтвердить.", show_alert=True)
        return

    await cb.answer("Подтверждено, монеты начислены.", show_alert=True)

    # после начисления — перечитываем
    a_after = get_assignment_full(aid)
    user_after = a_after.user
    coins_after = user_after.coins or 0
    lvl_after = level_by_coins(coins_after).level

    # уведомим пользователя
    try:
        # базовое уведомление
        await cb.bot.send_message(
            user_after.tg_id,
            f"✅ Ваше задание <b>{a_after.task.title}</b> проверено. Начислено <b>+{a_after.task.reward_coins}</b> coins!",
        )
        # если ап — отдельное сообщение
        if lvl_after > lvl_before:
            await cb.bot.send_message(
                user_after.tg_id,
                f"🎉 <b>Level up!</b>\nТеперь у вас <b>Level {lvl_after}</b>.",
            )

            badges = newly_unlocked_badge(lvl_before, lvl_after)
            if badges:
                await cb.bot.send_message(
                    user_after.tg_id,
                    f"{badges.icon} <b>Badges unlocked:<b> {badges.title}",
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
            f"❌ Ваше задание <b>{a.task.title}</b> отклонено.\nПопробуйте ещё раз — уточните детали и пришлите новый вариант.",
        )
    except Exception:
        pass


# Mentors


# Вход в раздел управления менторами
@router.callback_query(IsAdmin(), F.data == "admin:mentors")
async def admin_mentors_root(cb: CallbackQuery):
    await cb.message.edit_text(
        "🧑‍🏫 Управление менторами", reply_markup=admin_mentors_root_kb()
    )
    await cb.answer()


# Кнопка назад в общий админ-панель
@router.callback_query(IsAdmin(), F.data == "admin:panel")
async def admin_panel_home(cb: CallbackQuery):
    await cb.message.edit_text("⚙️ Админ-панель", reply_markup=admin_panel_kb())
    await cb.answer()


# ➕ Добавить ментора — шаг 1: спросить идентификатор
@router.callback_query(IsAdmin(), F.data == "admin:mentors:add")
async def mentor_add_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AdminMentorAdd.waiting_identifier)
    await cb.message.edit_text(
        "Отправь @username или tg_id пользователя, которого сделать ментором."
    )
    await cb.answer()


# ➕ Добавить ментора — шаг 2: принять идентификатор и спросить роль
@router.message(IsAdmin(), AdminMentorAdd.waiting_identifier)
async def mentor_add_got_identifier(msg: Message, state: FSMContext):
    ident = msg.text.strip()
    u = find_user(ident)
    if not u:
        # если никогда не виделись, можно создать «пустого» пользователя по id (для username создать нельзя)
        if ident.isdigit():
            u = get_or_create_user(int(ident))
        else:
            await msg.answer(
                "Не нашёл пользователя. Пришли @username или цифровой tg_id."
            )
            return
    await state.update_data(tg_id=u.tg_id)
    await msg.answer(
        f"Найден пользователь: @{u.username or '—'} (id={u.tg_id}). Выбери роль:",
        reply_markup=mentor_role_kb(u.tg_id),
    )


# обработчик кнопок выбора роли
@router.callback_query(IsAdmin(), F.data.startswith("admin:mentors:setrole:"))
async def mentor_set_role(cb: CallbackQuery, state: FSMContext):
    _, _, _, tg_id_str, role = cb.data.split(":")
    tg_id = int(tg_id_str)
    u = set_user_role(tg_id, role)
    if not u:
        await cb.answer("Пользователь не найден")
        return
    await state.clear()
    await cb.message.edit_text(
        f"✅ Назначен ментор: id={tg_id}, роль={role}",
        reply_markup=admin_mentors_root_kb(),
    )
    await cb.answer()


# 🗑 Удалить ментора — шаг 1
@router.callback_query(IsAdmin(), F.data == "admin:mentors:remove")
async def mentor_remove_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AdminMentorRemove.waiting_identifier)
    await cb.message.edit_text("Отправь @username или tg_id, чтобы снять роль ментора.")
    await cb.answer()


# 🗑 Удалить ментора — шаг 2
@router.message(IsAdmin(), AdminMentorRemove.waiting_identifier)
async def mentor_remove_got_identifier(msg: Message, state: FSMContext):
    ident = msg.text.strip()
    u = find_user(ident)
    if not u:
        await msg.answer("Не нашёл пользователя.")
        return
    set_user_role(u.tg_id, None)
    await state.clear()
    await msg.answer(
        f"✅ Роль ментора снята: @{u.username or '—'} (id={u.tg_id})",
        reply_markup=admin_mentors_root_kb(),
    )


# 📋 Список менторов
@router.callback_query(IsAdmin(), F.data == "admin:mentors:list")
async def mentor_list_view(cb: CallbackQuery):
    mentors = get_mentor_list()
    if not mentors:
        await cb.message.edit_text(
            "Пока нет менторов.", reply_markup=admin_mentors_root_kb()
        )
        return await cb.answer()
    lines = []
    for m in mentors:
        title = f"@{m.username}" if m.username else f"id={m.tg_id}"
        lines.append(f"• {title} — {m.role}")
    await cb.message.edit_text(
        "📋 Список менторов:\n\n" + "\n".join(lines),
        reply_markup=admin_mentors_root_kb(),
    )
    await cb.answer()


@router.message(Command("make_admin"))
async def make_admin_handler(msg: Message):
    """
    /make_admin <telegram_id>
    Команда только для СУПЕР-админов из ADMIN_IDS (в .env).
    """
    settings = get_settings()
    super_admins = set(settings.admin_ids or [])

    # 1. Проверяем, что вызывающий — супер-админ
    if msg.from_user.id not in super_admins:
        await msg.answer("❌ У тебя нет прав выдавать админку.")
        return

    parts = msg.text.split()
    if len(parts) != 2:
        await msg.answer(
            "Использование: /make_admin <telegram_id>\nПример: /make_admin 8007710555"
        )
        return

    try:
        target_tg_id = int(parts[1])
    except ValueError:
        await msg.answer("❌ Telegram ID должен быть числом.")
        return

    ok = set_admin_status(target_tg_id, True)
    if not ok:
        await msg.answer(
            f"❌ Пользователь с tg_id={target_tg_id} не найден в базе.\n"
            f"Пусть он сначала нажмёт /start у бота."
        )
        return

    await msg.answer(f"✅ Пользователь {target_tg_id} теперь администратор.")


@router.message(Command("last_users"))
async def last_users_handler(msg: Message):
    """
    Только для супер-админов.
    Показывает последних 20 пользователей: tg_id, username, роль, админ/нет.
    """
    settings = get_settings()
    super_admins = set(settings.admin_ids or [])

    if msg.from_user.id not in super_admins:
        await msg.answer("❌ У тебя нет прав смотреть список пользователей.")
        return

    users = get_recent_users(limit=20)
    if not users:
        await msg.answer("Пользователей в базе пока нет.")
        return

    lines = []
    for u in users:
        admin_flag = "🛡" if getattr(u, "is_admin", False) else "—"
        uname = f"@{u.username}" if u.username else "—"
        lines.append(f"{admin_flag} {u.tg_id} · {uname} · {u.role or '—'}")

    text = "👥 <b>Последние пользователи</b>:\n" + "\n".join(lines)
    await msg.answer(text)
