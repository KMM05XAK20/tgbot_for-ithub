from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
from ...services.tasks import list_tasks, list_public_tasks, get_task, take_task,  has_active_assignment, seed_tasks_if_empty, get_active_assignment
from ...keyboards.common import tasks_filters_kb, tasks_catalog_kb, task_view_kb, task_details_kb, main_menu_kb
from ...utils.telegram import safe_edit_text
from ...storage.models import Task


router = Router(name="tasks_catalog")


def render_tasks_list(tasks: list[Task], title: str = "📚 Каталог заданий") -> str:
    """
    Строит текстовый список заданий для каталога.
    Показывает награду, дедлайн и человеческую сложность.
    """
    if not tasks:
        return f"{title}\n\nПока нет заданий в этой категории."

    diff_labels = {
        "easy": "• 🟢 <b>Лёгкие</b> — чтобы втянуться и набрать первые coins\n",
        "medium": "• 🟡 <b>Средние</b> — базовый рабочий уровень\n",
        "hard": "• 🔴 <b>Сложные</b> — для тех, кто хочет максимум челленджа\n\n",
    }

    lines: list[str] = [title, ""]

    for t in tasks:
        diff_code = getattr(t, "difficulty", None)
        diff_human = diff_labels.get(diff_code, "⚪️ Без метки")

        reward = getattr(t, "reward_coins", None) or 0
        dd = getattr(t, "deadline_days", None)
        deadline_part = f"\n  ⏱ Дедлайн: {dd} дн." if dd else ""

        lines.append(
            f"• <b>{diff_human}</b>\n"
            f"  🎯 Сложность: {t.title}\n"
            f"  💰 Награда: {reward} coins"
            f"{deadline_part}\n"
            f"  ID: {t.id}"
        )

    return "\n\n".join(lines)

def difficulty_label(diff: str | None) -> str:
    mapping = {
    "easy": "🟢 Лёгкое",
    "medium": "🟡 Среднее",
    "hard": "🔴 Сложное",
    }

    return mapping.get((diff or "").lower(), "⚪ Без категории")

def render_task_card(t: Task) -> str:
    """
    Полная карточка задания: заголовок, сложность, награда, дедлайн, описание.
    """
    diff_labels = {
        "easy": "🟢 Лёгкое",
        "medium": "🟡 Среднее",
        "hard": "🔴 Сложное",
    }
    diff_human = diff_labels.get(t.difficulty or "", "⚪️ Без метки")

    reward = getattr(t, "reward_coins", None) or 0
    dd = getattr(t, "deadline_days", None)

    lines: list[str] = []

    lines.append(f"📌 <b>{t.title}</b>")
    lines.append(f"🎯 Сложность: {diff_human}")
    lines.append(f"💰 Награда: {reward} coins")

    if dd:
        lines.append(f"⏱ Дедлайн: {dd} дн.")

    desc = (t.description or "").strip()
    if desc:
        lines.append("")
        lines.append(f"📝 <b>Описание:</b>\n{desc}")

    lines.append("")
    lines.append(f"ID задания: <code>{t.id}</code>")

    return "\n".join(lines)


@router.callback_query(F.data == "menu:open:tasks")
async def open_tasks_root(cb: CallbackQuery):
    tasks = list_public_tasks(difficulty="all")
    text = render_tasks_list(tasks, title="📚 Каталог заданий")
    kb = tasks_catalog_kb(tasks)

    await safe_edit_text(
        cb.message,
        text,
        reply_markup=kb,
        parse_mode=ParseMode.HTML
    )
    await cb.answer()


@router.callback_query(F.data.startswith("tasks:view:"))
async def open_task_details(cb: CallbackQuery):
    # callback вида: tasks:open:2
    try:
        task_id = int(cb.data.split(":")[2])
    except (ValueError, IndexError):
        await cb.answer("Неверный формат callback.", show_alert=True)
        return

    t = get_task(task_id)
    if not t:
        await cb.answer("Задание не найдено.", show_alert=True)
        return

    # вот тут решаем, что показывать — «Взять» или «Сдать»
    already = has_active_assignment(cb.from_user.id, task_id)

    desc = (t.description or "").strip() if t.description else "—"
    difficulty = getattr(t, "difficulty", None) or "—"
    reward = t.reward_coins or 0

    text = (
        f"📌 <b>{t.title}</b>\n"
        f"🧩 Сложность: <b>{difficulty}</b>\n"
        f"💰 Награда: <b>{reward} coins</b>\n\n"
        f"<b>Описание:</b>\n{desc}"
    )

    await safe_edit_text(
        cb.message,
        text,
        reply_markup=task_view_kb(task_id, already_taken=already),
        parse_mode=ParseMode.HTML,
    )
    await cb.answer()


@router.callback_query(F.data.startswith("tasks:filter:"))
async def filter_tasks(cb: CallbackQuery):
    _, _, diff = cb.data.split(":", 2)  # easy / medium / hard / all

    difficulty = diff if diff != "all" else None
    tasks = list_public_tasks(difficulty=difficulty)

    title_map = {
        "easy": "🟢 Лёгкие задания",
        "medium": "🟡 Средние задания",
        "hard": "🔴 Сложные задания",
        "all": "📚 Все задания",
    }
    title = title_map.get(diff, "📚 Каталог заданий")

    text = render_tasks_list(tasks, title=title)

    await safe_edit_text(
        cb.message,
        text,
        reply_markup=tasks_catalog_kb(tasks),
    )
    await cb.answer()

@router.callback_query(F.data.startswith("task:view:"))
async def view_task(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[2])
    t = get_task(task_id)
    if not t:
        await cb.answer("Задание не найдено")
        return
    
    title = getattr(t, "title", getattr(t, "name", f"task #{task_id}"))
    reward = getattr(t, "reward", getattr(t, "coins", "—"))
    deadline_text = getattr(t, "deadline_text", "—")
    description = getattr(t, "description", "Без описания")

    
    text = (
        f"📱 <b>{title}</b>\n"
        f"💰 Награда: {reward} coins\n"
        f"⏱ Дедлайн: {deadline_text}\n\n"
        f"{description}"
    )
    await cb.message.edit_text(text, reply_markup=task_details_kb(task_id), parse_mode=ParseMode.HTML)
    await cb.answer()


def _difficulty_title(code: str) -> str:
    return {"easy": "🟢 Легкие", "medium": "🟡 Средние", "hard": "🔴 Сложные"}.get(code, "🗂 Все")


@router.callback_query(F.data == "tasks:filter:easy")
async def tasks_easy(cb: CallbackQuery):
    tasks = list_public_tasks(difficulty="easy")
    text = render_tasks_list(tasks, title="🟢 Лёгкие задания")
    await cb.message.edit_text(text, reply_markup=tasks_filters_kb())
    await cb.answer()


@router.callback_query(F.data == "tasks:filter:medium")
async def tasks_medium(cb: CallbackQuery):
    tasks = list_public_tasks(difficulty="medium")
    text = render_tasks_list(tasks, title="🟡 Средние задания")
    await cb.message.edit_text(text, reply_markup=tasks_filters_kb())
    await cb.answer()


@router.callback_query(F.data == "tasks:filter:hard")
async def tasks_hard(cb: CallbackQuery):
    tasks = list_public_tasks(difficulty="hard")
    text = render_tasks_list(tasks, title="🔴 Сложные задания")
    await cb.message.edit_text(text, reply_markup=tasks_filters_kb())
    await cb.answer()

# @router.callback_query(F.data.startswith("tasks:view:"))
# async def view_task(cb: CallbackQuery):
#     task_id = int(cb.data.split(":")[2])
#     t = get_task(task_id)
#     if not t:
#         await cb.answer("Задание не найдено")
#         return
#     text = (
#         f"📱 <b>{t['title']}</b>\n"
#         f"💰 Награда: {t['reward']} coins\n"
#         f"⏱ Дедлайн: {t.get('deadline_text','—')}\n\n"
#         f"{t.get('description','Без описания')}"
#     )
#     await cb.message.edit_text(text, reply_markup=task_details_kb(task_id), parse_mode=ParseMode.HTML)
#     await cb.answer()


# fake-copy function
# @router.callback_query(F.data.startswith("tasks:view:"))
# async def view_task(cb: CallbackQuery):
#     task_id = int(cb.data.split(":")[-1])
#     t = get_task(task_id)
#     if not t:
#         await cb.message.edit_text("Задание не найдено.", reply_markup=main_menu_kb())
#         return await cb.answer()

#     text = (
#         f"📌 <b>{t.title}</b>\n\n"
#         f"{t.description or 'Без описания'}\n\n"
#         f"Сложность: {_difficulty_title(t.difficulty)}\n"
#         f"Награда: <b>+{t.reward_coins} coins</b>\n"
#         f"Дедлайн: {t.deadline_hours} ч"
#     )
#     await cb.message.edit_text(text, reply_markup=task_details_kb(t.id))
#     await cb.answer()



@router.callback_query(F.data.startswith("tasks:take:"))
async def take_task_cb(cb: CallbackQuery):
    """
    Пользователь нажал 'Взять задание' в карточке.
    """
    try:
        task_id = int(cb.data.split(":")[2])
    except (IndexError, ValueError):
        await cb.answer("Некорректный ID задания.", show_alert=True)
        return

    user_id = cb.from_user.id

    # Проверяем, нет ли уже активного назначения по ЭТОМУ заданию
    if has_active_assignment(user_id, task_id):
        await cb.answer("У тебя уже есть это задание в работе.", show_alert=True)
        return

    # Пробуем выдать задание
    ok = take_task(user_id, task_id)
    if not ok:
        await cb.answer("Не удалось выдать задание. Попробуй позже.", show_alert=True)
        return

    t = get_task(task_id)
    if not t:
        await cb.answer("Задание не найдено.", show_alert=True)
        return

    text = render_task_card(t)

    await safe_edit_text(
        cb.message,
        text,
        reply_markup=task_view_kb(task_id, already_taken=True),
    )
    await cb.answer("Задание добавлено в твои активные ✅")

# @router.callback_query()
# async def debug_all_callback(cb: CallbackQuery):
#     print(f"[DEBUG TASK CALLBACK] {cb.data}")
#     await cb.answer()


# @router.callback_query(F.data.startswith("tasks:take:"))
# async def take_task_cb(cb: CallbackQuery):
#     task_id = int(cb.data.split(":")[2])

#     # Запрет брать новое, если есть активное (если у тебя есть такая логика)
#     if has_active_assignment(cb.from_user.id):
#         await cb.answer("У тебя уже есть активное задание. Заверши его прежде чем брать новое.", show_alert=True)
#         return

#     ok = take_task(user_tg_id=cb.from_user.id, task_id=task_id)
#     if not ok:
#         await cb.answer("Не удалось взять задание. Возможно, его уже взяли.", show_alert=True)
#         return

#     await cb.message.edit_text(
#         "✅ Задание взято!\nИнструкции отправлены в личные сообщения (или смотри раздел «Активные» в профиле).",
#         reply_markup=main_menu_kb()
#     )
#     await cb.answer()
# @router.callback_query(F.data.startswith("tasks:more:"))
# async def task_more(cb: CallbackQuery):
#     task_id = int(cb.data.split(":")[-1])
#     t = get_task(task_id)
#     if not t:
#         await cb.answer("Задание не найдено.", show_alert=True)
#         return

#     text = (
#         f"ℹ️ <b>Подробнее о задании</b>\n\n"
#         f"Название: <b>{t.title}</b>\n"
#         f"Описание: {t.description or '—'}\n"
#         f"Сложность: {_difficulty_title(t.difficulty)}\n"
#         f"Награда: +{t.reward_coins} coins\n"
#         f"Дедлайн: {t.deadline_hours} ч\n"
#         f"Статус: {t.status}"
#     )

#     already = has_active_assignment(cb.from_user.id, task_id)
#     await cb.message.edit_text(text, reply_markup=task_details_kb(task_id, already_taken=already))
#     await cb.answer()
