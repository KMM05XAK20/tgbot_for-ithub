from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command


from ...states.task_submit import TaskSubmit
from ...services.tasks import (
    get_active_assignment,
    submit_task,
    has_active_assignment,
)
from ...keyboards.common import main_menu_kb, task_view_kb

router = Router(name="tasks_submit")


@router.callback_query(F.data.startswith("tasks:submit:"))
async def submit_start(cb: CallbackQuery, state: FSMContext):
    """
    Нажали кнопку «📤 Сдать задание» под карточкой.
    Переводим пользователя в состояние ожидания доказательства.
    """
    try:
        task_id = int(cb.data.split(":")[2])
    except (ValueError, IndexError):
        await cb.answer("⚠ Неверный формат callback.", show_alert=True)
        return

    assignment = get_active_assignment(cb.from_user.id, task_id)
    if not assignment:
        await cb.answer("Сначала возьмите задание.", show_alert=True)
        return

    # сохраняем в FSM id назначения и задания
    await state.update_data(assignment_id=assignment.id, task_id=task_id)
    await state.set_state(TaskSubmit.waiting_proof)

    text = (
        "📤 <b>Сдать задание</b>\n\n"
        "Пришлите ссылку/описание (текст) или фото-доказательство.\n"
        "• Текст: отправьте одним сообщением\n"
        "• Фото: приложите как изображение\n\n"
        "Отмена: /cancel"
    )
    await cb.message.edit_text(text)
    await cb.answer()


@router.message(TaskSubmit.waiting_proof, F.text)
async def submit_text(message: Message, state: FSMContext):
    """
    Пользователь в состоянии waiting_proof присылает текст (ссылку, описание).
    """
    data = await state.get_data()
    task_id = data.get("task_id")

    ok = submit_task(
        user_tg_id=message.from_user.id,
        task_id=task_id,
        text=message.text,
        file_id=None,
    )
    if not ok:
        await message.answer("⚠ Не получилось сохранить сдачу. Попробуй ещё раз позже.")
        return

    await state.clear()

    # важное место: считаем, что задание всё ещё "активное/отправлено"
    already = has_active_assignment(message.from_user.id, task_id)
    await message.answer(
        "✅ Доказательство принято! Статус: <b>submitted</b>\nОжидайте проверки модератором.",
        reply_markup=task_view_kb(task_id, already_taken=already),
    )


@router.message(TaskSubmit.waiting_proof, F.photo)
async def submit_photo(message: Message, state: FSMContext):
    """
    Пользователь в состоянии waiting_proof присылает фото.
    """
    data = await state.get_data()
    task_id = data.get("task_id")

    largest = sorted(message.photo, key=lambda p: p.file_size or 0)[-1]

    ok = submit_task(
        user_tg_id=message.from_user.id,
        task_id=task_id,
        text=None,
        file_id=largest.file_id,
    )
    if not ok:
        await message.answer("⚠ Не получилось сохранить фото. Попробуй ещё раз позже.")
        return

    await state.clear()

    already = has_active_assignment(message.from_user.id, task_id)
    await message.answer(
        "✅ Фото получено! Статус: <b>submitted</b>\nОжидайте проверки модератором.",
        reply_markup=task_view_kb(task_id, already_taken=already),
    )


@router.message(TaskSubmit.waiting_proof)
async def fallback_any(message: Message):
    """
    Ловим любые другие типы сообщений в состоянии waiting_proof.
    """
    await message.answer(
        "Пожалуйста, отправьте текст (ссылку/описание) или фото. Для отмены — /cancel"
    )


@router.message(Command("cancel"))
async def cancel_submit(message: Message, state: FSMContext):
    """
    Универсальная отмена сдачи задания.
    """
    await state.clear()
    await message.answer(
        "Отменено. Вернулся в главное меню.", reply_markup=main_menu_kb()
    )
