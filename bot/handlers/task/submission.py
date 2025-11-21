from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.enums import ParseMode

from ...states.task_submit import TaskSubmit
from ...services.tasks import get_active_assignment, submit_task, has_active_assignment
from ...keyboards.common import main_menu_kb, task_view_kb  # task_view_kb должен принимать хотя бы task_id

router = Router(name="tasks_submit")


@router.callback_query(F.data.startswith("tasks:submit:"))
async def submit_start(cb: CallbackQuery, state: FSMContext):
    """Старт сдачи: проверяем, что задание активно, просим доказательство."""
    task_id = int(cb.data.split(":")[2])

    assignment = get_active_assignment(cb.from_user.id, task_id)
    if not assignment:
        await cb.answer("Сначала возьмите это задание.", show_alert=True)
        return

    # сохраняем только task_id — assignment_id не нужен для submit_task
    await state.update_data(task_id=task_id)
    await state.set_state(TaskSubmit.waiting_proof)

    text = (
        "📤 <b>Сдать задание</b>\n"
        "Пришлите ссылку/описание (текст) или фото/документ как доказательство.\n"
        "• Текст — одним сообщением\n"
        "• Фото — приложите изображение\n"
        "• Документ — прикрепите файл\n\n"
        "Отмена: /cancel"
    )
    await cb.message.edit_text(text, parse_mode=ParseMode.HTML)
    await cb.answer()


@router.message(TaskSubmit.waiting_proof, F.text)
async def submit_text(message: Message, state: FSMContext):
    """Получаем текст-доказательство и отправляем на модерацию."""
    data = await state.get_data()
    task_id = data.get("task_id")
    proof_text = (message.text or "").strip()
    if not task_id or not proof_text:
        return await message.answer("Нужно прислать текст/ссылку. Попробуйте ещё раз.")

    ok = submit_task(
        user_tg_id=message.from_user.id,
        task_id=task_id,
        text=proof_text,
        file_id=None,
    )
    await state.clear()

    if ok:
        await message.answer(
            "✅ Доказательство принято! Статус: <b>submitted</b>\nОжидайте проверки модератором.",
            reply_markup=task_view_kb(task_id),
            parse_mode=ParseMode.HTML,
        )
    else:
        await message.answer(
            "Не удалось отправить. Убедитесь, что задание у вас активно.",
            reply_markup=main_menu_kb(),
        )


@router.message(TaskSubmit.waiting_proof, F.photo | F.document)
async def submit_file(message: Message, state: FSMContext):
    """Получаем фото/документ как доказательство и отправляем на модерацию."""
    data = await state.get_data()
    task_id = data.get("task_id")
    if not task_id:
        return await message.answer("Что-то пошло не так, попробуйте /cancel и начните заново.")

    # берём file_id
    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id  # самое большое фото

    ok = submit_task(
        user_tg_id=message.from_user.id,
        task_id=task_id,
        text="(см. вложение)",
        file_id=file_id,
    )
    await state.clear()

    if ok:
        await message.answer(
            "✅ Файл получен! Статус: <b>submitted</b>\nОжидайте проверки модератором.",
            reply_markup=task_view_kb(task_id),
            parse_mode=ParseMode.HTML,
        )
    else:
        await message.answer(
            "Не удалось отправить. Убедитесь, что задание у вас активно.",
            reply_markup=main_menu_kb(),
        )


@router.message(TaskSubmit.waiting_proof)
async def submit_fallback(message: Message):
    """Если прислали что-то иное — подсказываем формат."""
    await message.answer("Пожалуйста, отправьте текст/ссылку, фото или документ. Для отмены — /cancel.")


@router.message(Command("cancel"))
async def cancel_submit(message: Message, state: FSMContext):
    """Универсальная отмена шага сдачи."""
    await state.clear()
    await message.answer("Отменено. Возвращаю в меню.", reply_markup=main_menu_kb())
