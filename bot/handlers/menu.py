from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from ..keyboards.common import main_menu_kb

router = Router(name="menu")

# SECTION_TEXTS = {
#     "profile": "👤 Профиль\nТвои баллы: {coins} coins\nТвой рейтинг: {position} место\n(Данные появятся после подключения БД)",
#     "tasks": "📚 Каталог заданий\nФильтры и задания добавим на следующем шаге.",
#     "rating": "🏆 Рейтинг\nТоп-10 и позиция пользователя — позже.",
#     "mentorship": "🤝 Менторство\nЗаявка и уведомления — позже.",
#     "calendar": "🗓️ Календарь\nСобытия и напоминания — позже.",
#     "courses": "🎯 Прокачка\nКурсы и рекомендации — позже.",
#     "help": "⚙️ Помощь\nFAQ и контакты — позже.",
# }

@router.callback_query(F.data == "menu:open:main")
async def open_main_menu(cb: CallbackQuery):
    text = (
        "🏠 <b>Главное меню</b>\n\n"
        "Что хочешь сделать сейчас?\n\n"
        "• 📚 <b>Каталог заданий</b> — бери задачи, выполняй и зарабатывай coins\n"
        "• 👤 <b>Профиль</b> — смотри свои уровни, бейджи и историю активности\n"
        "• 🏆 <b>Рейтинг</b> — следи за лидерами сообщества\n"
        "• 🧑‍🏫 <b>Менторство</b> — выбирай наставника или стань им сам\n"
        "• 📅 <b>Календарь</b> — важные события и дедлайны\n"
        "• ❓ <b>Помощь</b> — описание команд и ролей\n"
    )
    await cb.message.edit_text(text, reply_markup=main_menu_kb())
    await cb.answer()


# async def on_menu_open(cb: CallbackQuery):
#     section = cb.data.split(":")[-1]
#     text = SECTION_TEXTS.get(section, "Раздел в разработке.")
#     await cb.message.edit_text(text + "\n\n⬅️ Вернуться в главное меню:", reply_markup=main_menu_kb())
#     await cb.answer()

@router.message(Command("cancel"))
async def cancel_any(message:Message, state:FSMContext):
    await state.clear()
    await message.answer("Отменил. Возвращаю в главное меню", reply_markup=main_menu_kb)