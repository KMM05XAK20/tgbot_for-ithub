from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
from ...services.tasks import list_tasks, get_task, take_task,  has_active_assignment, seed_tasks_if_empty, get_active_assignment
from ...keyboards.common import tasks_filters_kb, tasks_list_kb, task_details_kb, main_menu_kb
from ...utils.telegram import safe_edit_text


router = Router(name="tasks_catalog")


@router.callback_query(F.data == "menu:open:tasks")
async def open_tasks_root(cb: CallbackQuery):
    # на всякий случай — если в базе нет заданий, подсеять примеры
    seed_tasks_if_empty()
    text = (
        "📚 <b>Каталог заданий</b>\n"
        "Выбери уровень сложности, чтобы посмотреть задания.\n\n"
        "• 🟢 Лёгкие (1–5 coins)\n"
        "• 🟡 Средние (5–10 coins)\n"
        "• 🔴 Сложные (10–15 coins)\n"
    )
    await safe_edit_text(cb.message, text, reply_markup=tasks_filters_kb(), ParseMode=ParseMode.HTML)
    await cb.answer()

@router.callback_query(F.data.startswith("task:filter:"))
async def filter_tasks(cb: CallbackQuery):
    diff = cb.data.split(":",)[2] #e|n or m |h
    ranges = {"easy": (1,2), "medium": (5, 10), "hard": (10, 15)}
    min_c, max_c = ranges.get(diff, (None, None))

    tasks = list_tasks(min_reward=min_c, max_reward=max_c, difficulty=diff, only_published=True)
    if not tasks:
        await cb.message.edit_text("Пока нет заданий в этой категории.", reply_markup=tasks_filters_kb())
        await cb.answer()

        mark = "🟢" if diff == "easy" else "🟡" if diff == "medium" else "🔴"
        await safe_edit_text(
            cb.message,
            f"📚 Задания {mark}\nВыбери задание:",
            reply_markup=tasks_list_kb(tasks),
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
    task_id = int(cb.data.split(":")[2])

    # Запрет брать новое, если есть активное (если у тебя есть такая логика)
    if has_active_assignment(cb.from_user.id):
        await cb.answer("У тебя уже есть активное задание. Заверши его прежде чем брать новое.", show_alert=True)
        return

    ok = take_task(user_tg_id=cb.from_user.id, task_id=task_id)
    if not ok:
        await cb.answer("Не удалось взять задание. Возможно, его уже взяли.", show_alert=True)
        return

    await cb.message.edit_text(
        "✅ Задание взято!\nИнструкции отправлены в личные сообщения (или смотри раздел «Активные» в профиле).",
        reply_markup=main_menu_kb()
    )
    await cb.answer()
@router.callback_query(F.data.startswith("tasks:more:"))
async def task_more(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[-1])
    t = get_task(task_id)
    if not t:
        await cb.answer("Задание не найдено.", show_alert=True)
        return

    text = (
        f"ℹ️ <b>Подробнее о задании</b>\n\n"
        f"Название: <b>{t.title}</b>\n"
        f"Описание: {t.description or '—'}\n"
        f"Сложность: {_difficulty_title(t.difficulty)}\n"
        f"Награда: +{t.reward_coins} coins\n"
        f"Дедлайн: {t.deadline_hours} ч\n"
        f"Статус: {t.status}"
    )

    already = has_active_assignment(cb.from_user.id, task_id)
    await cb.message.edit_text(text, reply_markup=task_details_kb(task_id, already_taken=already))
    await cb.answer()
