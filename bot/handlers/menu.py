from aiogram import Router, F
from aiogram.types import CallbackQuery
from ..keyboards.common import main_menu_kb

router = Router()

SECTION_TEXTS = {
    "profile": "👤 Профиль\nТвои баллы: {coins} coins\nТвой рейтинг: {position} место\n(Данные появятся после подключения БД)",
    "tasks": "📚 Каталог заданий\nФильтры и задания добавим на следующем шаге.",
    "rating": "🏆 Рейтинг\nТоп-10 и позиция пользователя — позже.",
    "mentorship": "🤝 Менторство\nЗаявка и уведомления — позже.",
    "calendar": "🗓️ Календарь\nСобытия и напоминания — позже.",
    "courses": "🎯 Прокачка\nКурсы и рекомендации — позже.",
    "help": "⚙️ Помощь\nFAQ и контакты — позже.",
}

@router.callback_query(F.data.startswith("menu:open:root"))
async def back_to_rootz(cd: CallbackQuery):
    await cd.message.edit_text("Главное меню:", reply_markup=main_menu_kb())
    await cd.answer()

async def on_menu_open(cb: CallbackQuery):
    section = cb.data.split(":")[-1]
    text = SECTION_TEXTS.get(section, "Раздел в разработке.")
    await cb.message.edit_text(text + "\n\n⬅️ Вернуться в главное меню:", reply_markup=main_menu_kb())
    await cb.answer()
