from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from ...filters.roles import IsAdmin
from ...keyboards.common import admin_tasks_root_kb, admin_tasks_list_kb
from ...services.tasks import (
    admin_list_all_tasks, admin_toggle_task_publised, admin_delete_task,
    admin_create_task, seed_tasks_if_empty
)
from ...states.tasks_admin import AdminTaskCreate

router = Router(name="admin_tasks")

# Вход в раздел
@router.callback_query(IsAdmin(), F.data == "admin:tasks")
async def admin_tasks_root(cb: CallbackQuery):
    await cb.message.edit_text("📚 Управление заданиями", reply_markup=admin_tasks_root_kb())
    await cb.answer()

# Список
@router.callback_query(IsAdmin(), F.data == "admin:tasks:list")
async def admin_tasks_list(cb: CallbackQuery):
    items = admin_list_all_tasks()
    if not items:
        await cb.message.edit_text("Заданий пока нет.", reply_markup=admin_tasks_root_kb())
        return await cb.answer()
    await cb.message.edit_text("📋 Список заданий:", reply_markup=admin_tasks_list_kb(items))
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
    await cb.message.edit_text("📋 Список заданий:", reply_markup=admin_tasks_list_kb(items))
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
        await cb.message.edit_text("Задание удалено. Список пуст.", reply_markup=admin_tasks_root_kb())
    else:
        await cb.message.edit_text("📋 Список заданий:", reply_markup=admin_tasks_list_kb(items))
    await cb.answer("Удалено")

# Засеять демо
@router.callback_query(IsAdmin(), F.data == "admin:tasks:seed")
async def admin_tasks_seed(cb: CallbackQuery):
    seed_tasks_if_empty()
    await cb.answer("Демо-набор проверен/засеян")
    items = admin_list_all_tasks()
    if not items:
        await cb.message.edit_text("Не удалось создать демо-набор.", reply_markup=admin_tasks_root_kb())
    else:
        await cb.message.edit_text("📋 Список заданий:", reply_markup=admin_tasks_list_kb(items))

# Создание — шаги FSM
@router.callback_query(IsAdmin(), F.data == "admin:tasks:add")
async def admin_tasks_add_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AdminTaskCreate.title)
    await cb.message.edit_text("Введите <b>заголовок</b> задания:", parse_mode="HTML")
    await cb.answer()

@router.message(IsAdmin(), AdminTaskCreate.title)
async def admin_tasks_add_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text.strip())
    await state.set_state(AdminTaskCreate.description)
    await msg.answer("Введите <b>описание</b> задания:", parse_mode="HTML")

@router.message(IsAdmin(), AdminTaskCreate.description)
async def admin_tasks_add_desc(msg: Message, state: FSMContext):
    await state.update_data(description=msg.text.strip())
    await state.set_state(AdminTaskCreate.reward)
    await msg.answer("Введите <b>награду</b> (целое число coins):", parse_mode="HTML")

@router.message(IsAdmin(), AdminTaskCreate.reward)
async def admin_tasks_add_reward(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        return await msg.answer("Нужно целое число. Введите награду ещё раз.")
    await state.update_data(reward=int(msg.text))
    await state.set_state(AdminTaskCreate.difficulty)
    await msg.answer("Введите <b>сложность</b>: easy | medium | hard", parse_mode="HTML")

@router.message(IsAdmin(), AdminTaskCreate.difficulty)
async def admin_tasks_add_diff(msg: Message, state: FSMContext):
    diff = msg.text.strip().lower()
    if diff not in {"easy", "medium", "hard"}:
        return await msg.answer("Допустимо: easy | medium | hard. Введите ещё раз.")
    await state.update_data(difficulty=diff)
    await state.set_state(AdminTaskCreate.deadline_days)
    await msg.answer("Введите <b>дедлайн в днях</b> (0 — без дедлайна):", parse_mode="HTML")

@router.message(IsAdmin(), AdminTaskCreate.deadline_days)
async def admin_tasks_add_deadline(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        return await msg.answer("Нужно целое число дней. Введите ещё раз.")
    await state.update_data(deadline_days=int(msg.text))
    data = await state.get_data()
    tid = admin_create_task(
        title=data["title"],
        description=data["description"],
        reward=data["reward"],
        difficulty=data["difficulty"],
        deadline_days=data["deadline_days"],
    )
    await state.clear()
    await msg.answer(f"✅ Задание создано (id={tid}). По умолчанию *скрыто*, опубликуйте в списке.",
                     reply_markup=admin_tasks_root_kb(), parse_mode="Markdown")

@router.callback_query(IsAdmin(), F.data.startswith("admin:tasks:nop:"))
async def admin_tasks_noop(cb: CallbackQuery):
    await cb.answer()