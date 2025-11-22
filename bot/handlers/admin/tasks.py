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
from ...states.tasks import TaskCreateStates
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
        #deadline_hours=deadline_hours,
    )

    await msg.answer(
        f"✅ Задание создано (ID: {task_id}).\n"
        f"Оно уже доступно в каталоге, сложность определена автоматически.",
        reply_markup=admin_tasks_root_kb(),
    )

@router.callback_query(IsAdmin(), F.data.startswith("admin:tasks:nop:"))
async def admin_tasks_noop(cb: CallbackQuery):
    await cb.answer()