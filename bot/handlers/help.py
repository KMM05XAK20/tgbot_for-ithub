# bot/handlers/help.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from ..keyboards.common import main_menu_kb

router = Router(name="help")


HELP_TEXT = (
    "⚙️ <b>Помощь</b>\n\n"
    "Этот бот — внутренняя платформа INFLUENCE.HUB.\n\n"
    "Основные разделы:\n"
    "• 👤 Профиль — твои coins, уровень, рейтинг и бейджи\n"
    "• 📚 Каталог заданий — задания разной сложности\n"
    "• 🏆 Рейтинг — топ участников\n"
    "• 🤝 Менторство — заявки на помощь от менторов\n"
    "• 🗓️ Календарь — ближайшие события\n\n"
    "Команды:\n"
    "• /start — главное меню\n"
    "• /whoime — информация о твоём профиле (id, роль, админ)\n"
)


@router.message(Command("help"))
async def help_command(msg: Message):
    await msg.answer(HELP_TEXT, reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:open:help")
async def help_from_menu(cb: CallbackQuery):
    await cb.message.edit_text(HELP_TEXT, reply_markup=main_menu_kb())
    await cb.answer()
