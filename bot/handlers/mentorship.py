from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from ..services.users import get_user
from ..services.mentorship import create_mentor_application, get_mentor_list
from ..storage.models import MentorTopic  # Добавляем импорт для MentorTopic

router = Router()

# Просмотр списка наставников
@router.message(Command("mentors"))
async def show_mentors(msg: Message):
    mentors = get_mentor_list()
    if not mentors:
        await msg.answer("Нет доступных наставников.")
        return

    # Создаем клавиатуру для выбора наставника
    buttons = [
        InlineKeyboardButton(text=f"{mentor.username} ({mentor.role})", callback_data=f"mentor:{mentor.id}")
        for mentor in mentors
    ]
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(*buttons)

    await msg.answer("Выберите наставника:", reply_markup=kb)
    
# Выбор наставника
@router.callback_query(F.data == "mentor:choose")
async def choose_mentor(cb: CallbackQuery):
    print("Callback received: ", cb.data)  # Для отладки
    mentors = get_mentor_list()
    if not mentors:
        await cb.answer("Нет доступных наставников.")
        return

    text = "Выберите наставника:\n"
    for mentor in mentors:
        text += f"{mentor.username} ({mentor.role})\n"

    buttons = [
        InlineKeyboardButton(text=f"{mentor.username}", callback_data=f"mentor:{mentor.id}")
        for mentor in mentors
    ]
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(*buttons)

    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()

# Отправка заявки на менторство
@router.callback_query(F.data.startswith("mentor:"))
async def mentor_callback(cb: CallbackQuery):
    mentor_id = int(cb.data.split(":")[1])
    topic = MentorTopic.CONTENT  # По умолчанию, или сделаем выбор темы
    user_id = cb.from_user.id

    # Проверка, что наставник существует
    mentor = get_user(mentor_id)
    if not mentor:
        await cb.answer("Наставник не найден.")
        return

    # Отправка заявки
    create_mentor_application(user_id=user_id, mentor_id=mentor_id, topic=topic)
    await cb.answer("Ваша заявка на менторство отправлена!")
