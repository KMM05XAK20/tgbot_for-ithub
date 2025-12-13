from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from ...filters.roles import IsAdmin
from ...keyboards.common import (
    admin_tasks_root_kb,
    admin_tasks_list_kb,
    admin_assignment_kb,
    admin_assignments_pending_kb,
)
from ...services.tasks import (
    admin_list_all_tasks,
    admin_toggle_task_publised,
    admin_delete_task,
    approve_assignment,
    reject_assignment,
    admin_create_task,
    seed_tasks_if_empty,
    list_pending_assignments,
    get_assignment_for_moderation,
    get_assignment_full,
)
from ...states.tasks import TaskCreateStates


router = Router(name="admin_tasks")


# Debug
@router.callback_query(F.data.startswith("admin:assign"))
async def debug_admin_assign(cb: CallbackQuery):
    print("[DEBUG ADMIN ASSIGN]", cb.data)


# Вход в раздел
@router.callback_query(IsAdmin(), F.data == "admin:tasks")
async def admin_tasks_root(cb: CallbackQuery):
    await cb.message.edit_text(
        "📚 Управление заданиями", reply_markup=admin_tasks_root_kb()
    )
    await cb.answer()


# Список
@router.callback_query(IsAdmin(), F.data == "admin:tasks:list")
async def admin_tasks_list(cb: CallbackQuery):
    items = admin_list_all_tasks()
    if not items:
        await cb.message.edit_text(
            "Заданий пока нет.", reply_markup=admin_tasks_root_kb()
        )
        return await cb.answer()
    await cb.message.edit_text(
        "📋 Список заданий:", reply_markup=admin_tasks_list_kb(items)
    )
    await cb.answer()


# Тоггл публикации
@router.callback_query(IsAdmin(), F.data.startswith("admin:tasks:toggle:"))
async def admin_tasks_toggle(cb: CallbackQuery):
    tid = int(cb.data.split(":")[-1])
    ok = admin_toggle_task_publised(tid)
    if not ok:
        return await cb.answer("Задание не найдено", show_alert=True)
    # перерисуем список
    items = admin_list_all_tasks()
    await cb.message.edit_text(
        "📋 Список заданий:", reply_markup=admin_tasks_list_kb(items)
    )
    await cb.answer("Статус обновлён")


# Удаление
@router.callback_query(IsAdmin(), F.data.startswith("admin:tasks:delete:"))
async def admin_tasks_delete(cb: CallbackQuery):
    tid = int(cb.data.split(":")[-1])
    ok = admin_delete_task(tid)
    if not ok:
        return await cb.answer("Задание не найдено", show_alert=True)
    items = admin_list_all_tasks()
    if not items:
        await cb.message.edit_text(
            "Задание удалено. Список пуст.", reply_markup=admin_tasks_root_kb()
        )
    else:
        await cb.message.edit_text(
            "📋 Список заданий:", reply_markup=admin_tasks_list_kb(items)
        )
    await cb.answer("Удалено")


@router.callback_query(F.data == "admin:assignments:pending")
async def admin_assignments_pending(cb: CallbackQuery):
    """
    Экран списка всех заданий в статусе 'submitted'.
    """
    items = list_pending_assignments()

    if not items:
        await cb.answer("Нет заданий на модерации 👍", show_alert=True)
        # Можно вернуть в админку
        await cb.message.edit_text(
            "Всё чисто. Заданий на модерации нет.", reply_markup=admin_tasks_root_kb()
        )
        return

    lines = ["🧾 <b>Задания на модерации</b>"]
    for ass in items:
        user = ass["user_username"] or ass["user_tg_id"]
        lines.append(f"• #{ass['id']} · {ass['task_title']} · @{user}")

    text = "\n".join(lines)
    await cb.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=admin_assignments_pending_kb(items),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("admin:assign:open:"))
async def admin_assign_open(cb: CallbackQuery):
    """
    Открыть одну конкретную сдачу для проверки.
    """
    try:
        assignment_id = int(cb.data.split(":")[3])
    except (IndexError, ValueError):
        await cb.answer("Неверный формат callback-data", show_alert=True)
        return

    ass = get_assignment_for_moderation(assignment_id)
    if not ass:
        await cb.answer(
            "Не нашёл это задание. Возможно, уже обработано.", show_alert=True
        )
        return

    user = ass["user_username"] or ass["user_tg_id"]
    reward = ass["reward"]

    text_lines = [
        f"🧾 <b>Проверка задания #{ass['id']}</b>",
        "",
        f"📌 Задание: <b>{ass['task_title']}</b>",
        f"👤 Участник: @{user}",
        f"💰 Награда: {reward} coins",
        "",
    ]

    if ass["submitted_at"]:
        text_lines.append(f"⏱ Отправлено: {ass['submitted_at']}")
        text_lines.append("")

    if ass["submission_text"]:
        text_lines.append("💬 <b>Ответ:</b>")
        text_lines.append(ass["submission_text"])
        text_lines.append("")

    if ass["submission_file_id"]:
        text_lines.append("🖼 Есть прикреплённое фото.")
        # если захочешь — можешь отдельным сообщением присылать photo по file_id
        text_lines.append("")

    text = "\n".join(text_lines)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"admin:assign:approve:{ass['id']}",
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"admin:assign:reject:{ass['id']}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ К списку",
                    callback_data="admin:assignments:pending",
                )
            ],
        ]
    )

    await cb.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("admin:assign:open:"))
async def admin_open_assignment(cb: CallbackQuery):
    print("[DEBUG ADMIN OPEN RAW]", cb.data)
    parts = cb.data.split(":")
    try:
        assignment_id = int(parts[-1])
    except ValueError:
        await cb.answer("Некорректный ID заявки.", show_alert=True)
        return

    info = get_assignment_full(assignment_id)
    if not info:
        await cb.answer("Заявка не найдена.", show_alert=True)
        return

    uname = info.get("user_username") or "без никнейма"
    uid = info.get("user_tg_id")
    task_title = info.get("task_title") or "без названия"
    reward = info.get("task_reward") or 0
    diff = info.get("task_difficulty") or "—"
    status = info.get("status")
    text = info.get("submission_text") or "—"
    submitted_at = info.get("submitted_at")

    submitted_str = submitted_at.strftime("%Y-%m-%d %H:%M") if submitted_at else "—"

    body = (
        "📝 <b>Заявка на задание</b>\n"
        f"👤 Пользователь: @{uname} (tg_id: {uid})\n"
        f"📌 Задание: <b>{task_title}</b>\n"
        f"🎯 Сложность: {diff}\n"
        f"💰 Награда: {reward} coins\n"
        f"📊 Статус: <b>{status}</b>\n"
        f"⏱ Отправлено: {submitted_str}\n\n"
        f"📎 Доказательство:\n{text}"
    )

    await cb.message.edit_text(
        body,
        reply_markup=admin_assignment_kb(assignment_id),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("admin:assign:approve:"))
async def admin_assign_approve(cb: CallbackQuery):
    try:
        assignment_id = int(cb.data.split(":")[3])
    except (IndexError, ValueError):
        await cb.answer("Неверный формат callback-data", show_alert=True)
        return

    ok = approve_assignment(assignment_id)
    if not ok:
        await cb.answer(
            "Не удалось одобрить (возможно, уже обработано).", show_alert=True
        )
        return

    await cb.answer("✅ Одобрено, монеты начислены!", show_alert=True)

    # Перерисуем список оставшихся
    items = list_pending_assignments()
    if not items:
        await cb.message.edit_text(
            "🎉 Все задания проверены!", reply_markup=admin_tasks_root_kb()
        )
    else:
        # переиспользуем функцию
        await admin_assignments_pending(cb)


@router.callback_query(F.data.startswith("admin:assign:reject:"))
async def admin_assign_reject(cb: CallbackQuery):
    try:
        assignment_id = int(cb.data.split(":")[3])
    except (IndexError, ValueError):
        await cb.answer("Неверный формат callback-data", show_alert=True)
        return

    ok = reject_assignment(assignment_id)
    if not ok:
        await cb.answer(
            "Не удалось отклонить (возможно, уже обработано).", show_alert=True
        )
        return

    await cb.answer("❌ Отклонено.", show_alert=True)

    items = list_pending_assignments()
    if not items:
        await cb.message.edit_text(
            "🎉 Все задания проверены!", reply_markup=admin_tasks_root_kb()
        )
    else:
        await admin_assignments_pending(cb)


# Засеять демо
@router.callback_query(IsAdmin(), F.data == "admin:tasks:seed")
async def admin_tasks_seed(cb: CallbackQuery):
    seed_tasks_if_empty()
    await cb.answer("Демо-набор проверен/засеян")
    items = admin_list_all_tasks()
    if not items:
        await cb.message.edit_text(
            "Не удалось создать демо-набор.", reply_markup=admin_tasks_root_kb()
        )
    else:
        await cb.message.edit_text(
            "📋 Список заданий:", reply_markup=admin_tasks_list_kb(items)
        )


# Создание — шаги FSM
@router.callback_query(F.data == "admin:tasks:add", IsAdmin())
async def admin_tasks_add_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(TaskCreateStates.waiting_title)
    await cb.message.edit_text("✏️ Введите заголовок задания:")
    await cb.answer()


# Шаг 1 — заголовок
@router.message(TaskCreateStates.waiting_title)
async def admin_tasks_add_title(msg: Message, state: FSMContext):
    title = msg.text.strip()
    if not title:
        await msg.answer("Заголовок не может быть пустым. Введите ещё раз:")
        return

    await state.update_data(title=title)
    await msg.answer("📝 Введите описание задания:")
    await state.set_state(TaskCreateStates.waiting_description)


# Шаг 2 — описание
@router.message(TaskCreateStates.waiting_description)
async def admin_tasks_add_description(msg: Message, state: FSMContext):
    desc = msg.text.strip()
    await state.update_data(description=desc)
    await msg.answer("💰 Введите награду в coins (целое число):")
    await state.set_state(TaskCreateStates.waiting_reward)


# Шаг 3 — награда
@router.message(TaskCreateStates.waiting_reward)
async def admin_tasks_add_reward(msg: Message, state: FSMContext):
    text = msg.text.strip()
    try:
        reward = int(text)
    except ValueError:
        await msg.answer("Награда должна быть числом. Попробуйте ещё раз:")
        return

    if reward <= 0:
        await msg.answer("Награда должна быть больше нуля. Попробуйте ещё раз:")
        return

    await state.update_data(reward=reward)
    await msg.answer("⏱ Введите дедлайн в днях (например, 2):")
    await state.set_state(TaskCreateStates.waiting_deadline)


# Шаг 4 — дедлайн и финальное сохранение
@router.message(TaskCreateStates.waiting_deadline)
async def admin_tasks_add_deadline(msg: Message, state: FSMContext):
    text = msg.text.strip()
    try:
        deadline_days = int(text)
    except ValueError:
        await msg.answer("Дедлайн должен быть числом (в днях). Попробуйте ещё раз:")
        return

    data = await state.get_data()
    await state.clear()

    title = data.get("title")
    description = data.get("description") or ""
    reward = data.get("reward")

    # ВАЖНО: здесь НИЧЕГО не спрашиваем про сложность —
    # она определяется автоматически по reward внутри admin_create_task
    task_id = admin_create_task(
        title=title,
        description=description,
        reward=reward,
        deadline_days=deadline_days,
        # deadline_hours=deadline_hours,
    )

    await msg.answer(
        f"✅ Задание создано (ID: {task_id}).\n"
        f"Оно уже доступно в каталоге, сложность определена автоматически.",
        reply_markup=admin_tasks_root_kb(),
    )


@router.callback_query(IsAdmin(), F.data.startswith("admin:tasks:nop:"))
async def admin_tasks_noop(cb: CallbackQuery):
    await cb.answer()
