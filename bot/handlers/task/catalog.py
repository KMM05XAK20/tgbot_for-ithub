from aiogram import Router, F
from aiogram.types import CallbackQuery
from ...keyboards.common import tasks_filters_kb, tasks_list_kb, task_view_kb, main_menu_kb
from ...services.tasks import list_tasks, get_task, take_task, has_active_assignment, seed_tasks_if_empty

router = Router()

def _difficulty_title(code: str) -> str:
    return {"easy": "🟢 Легкие", "medium": "🟡 Средние", "hard": "🔴 Сложные"}.get(code, "🗂 Все")

@router.callback_query(F.data == "menu:open:tasks")
async def open_tasks_root(cb: CallbackQuery):
    # Однократное наполнение тестовыми заданиями (безопасно)
    seed_tasks_if_empty()
    text = "📚 <b>Каталог заданий</b>\nВыбери сложность:"
    await cb.message.edit_text(text, reply_markup=tasks_filters_kb())
    await cb.answer()

@router.callback_query(F.data.startswith("tasks:filter:"))
async def open_tasks_list(cb: CallbackQuery):
    # data: tasks:filter:<difficulty|all>:<page>
    _, _, diff, page_str = cb.data.split(":")
    page = int(page_str)
    diff_arg = None if diff == "all" else diff
    tasks = list_tasks(diff_arg, page=page, per_page=5)
    items = [(t.id, f"{t.title} · +{t.reward_coins}c") for t in tasks]

    header = f"Каталог → {_difficulty_title(diff)} (стр. {page})"
    body = "Выберите задание:"
    text = f"📚 <b>{header}</b>\n{body}"

    await cb.message.edit_text(text, reply_markup=tasks_list_kb(diff, page, items))
    await cb.answer()

@router.callback_query(F.data.startswith("tasks:view:"))
async def view_task(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[-1])
    t = get_task(task_id)
    if not t:
        await cb.message.edit_text("Задание не найдено.", reply_markup=main_menu_kb())
        return await cb.answer()

    text = (
        f"📌 <b>{t.title}</b>\n\n"
        f"{t.description or 'Без описания'}\n\n"
        f"Сложность: {_difficulty_title(t.difficulty)}\n"
        f"Награда: <b>+{t.reward_coins} coins</b>\n"
        f"Дедлайн: {t.deadline_hours} ч"
    )
    await cb.message.edit_text(text, reply_markup=task_view_kb(t.id))
    await cb.answer()

@router.callback_query(F.data.startswith("tasks:take:"))
async def take_task_cb(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[-1])
    if has_active_assignment(cb.from_user.id, task_id):
        await cb.answer("У тебя уже есть это задание в работе.", show_alert=True)
        return
    ok = take_task(cb.from_user.id, task_id)
    if ok:
        await cb.answer("Задание добавлено в ваши активные.", show_alert=True)
    else:
        await cb.answer("Не удалось взять задание.", show_alert=True)
