from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from ...states.tasks import TaskSubmit
from ...services.tasks import get_active_assignment, submit_assignment_text, submit_assignment_file
from ...keyboards.common import main_menu_kb, task_view_kb
from ...services.tasks import get_task, has_active_assignment

router = Router()

@router.callback_query(F.data.startswith("tasks:submit:"))
async def start_submit(cb: CallbackQuery, state: FSMContext):
    task_id = int(cb.data.split(":")[-1])
    assignment = get_active_assignment(cb.from_user.id, task_id)
    if not assignment:
        await cb.answer("Сначала возьмите задание.", show_alert=True)
        return

    # Запомним assignment_id в FSM
    await state.update_data(assignment_id=assignment.id, task_id=task_id)
    await state.set_state(TaskSubmit.waiting_proof)

    text = (
        "📤 <b>Сдать задание</b>\n"
        "Пришлите ссылку/описание (текст) или фото-доказательство.\n"
        "• Текст: отправьте одним сообщением\n"
        "• Фото: приложите как изображение\n\n"
        "Отмена: /cancel"
    )
    await cb.message.edit_text(text)
    await cb.answer()

@router.message(TaskSubmit.waiting_proof, F.text)
async def submit_text(message: Message, state: FSMContext):
    data = await state.get_data()
    assignment_id = data.get("assignment_id")
    task_id = data.get("task_id")
    ok = submit_assignment_text(assignment_id, message.text)
    await state.clear()

    t = get_task(task_id)
    already = has_active_assignment(message.from_user.id, task_id)  # будет 'submitted', всё равно считаем активным
    await message.answer(
        "✅ Доказательство принято! Статус: <b>submitted</b>\nОжидайте проверки модератором.",
        reply_markup=task_view_kb(task_id, already_taken=already)
    )

@router.message(TaskSubmit.waiting_proof, F.photo)
async def submit_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    assignment_id = data.get("assignment_id")
    task_id = data.get("task_id")

    # берём наибольшее фото
    largest = sorted(message.photo, key=lambda p: p.file_size or 0)[-1]
    ok = submit_assignment_file(assignment_id, largest.file_id)
    await state.clear()

    already = has_active_assignment(message.from_user.id, task_id)
    await message.answer(
        "✅ Фото получено! Статус: <b>submitted</b>\nОжидайте проверки модератором.",
        reply_markup=task_view_kb(task_id, already_taken=already)
    )

@router.message(TaskSubmit.waiting_proof)
async def fallback_any(message: Message):
    await message.answer("Пожалуйста, отправьте текст (ссылку/описание) или фото. Для отмены — /cancel")

# Универсальная отмена
from aiogram.filters import Command

@router.message(Command("cancel"))
async def cancel_submit(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено. Вернулся в главное меню.", reply_markup=main_menu_kb())
