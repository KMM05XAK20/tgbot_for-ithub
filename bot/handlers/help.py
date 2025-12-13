# bot/handlers/help.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from ..services.users import get_user
from ..keyboards.common import main_menu_kb, admin_grant_kb
from ..config import get_settings

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
    "• /help - информация о боте (аналогична кнопке 'Помощь')\n"
    "• Чтобы сообщить об ошибках в боте писать сюда - @mkm1950\n Желательно приложить скрин"
)


@router.callback_query(F.data == "menu:open:help")
async def open_help_menu(cb: CallbackQuery):
    await cb.message.edit_text(HELP_TEXT, reply_markup=main_menu_kb())
    await cb.answer()


@router.message(Command("help"))
async def help_command(msg: Message):
    await msg.answer(HELP_TEXT, reply_markup=main_menu_kb())


@router.message(Command("whoime"))
async def whoime(msg: Message):
    user = get_user(msg.from_user.id)
    settings = get_settings()

    text = (
        f"🆔 {msg.from_user.id}\n"
        f"👤 @{msg.from_user.username}\n"
        f"🎭 Роль: {user.role}\n"
        f"🪙 Coins: {user.coins}\n"
        f"🛡 Админ: {'да' if user.is_admin else 'нет'}\n"
        f"👑 Супер-админ: {'да' if msg.from_user.id in settings.admin_ids else 'нет'}"
    )

    # Если вызывающий — супер-админ → показать кнопки
    if msg.from_user.id in settings.admin_ids:
        await msg.answer(text, reply_markup=admin_grant_kb(msg.from_user.id))
    else:
        await msg.answer(text)


@router.message(Command("help"))
async def help_command(msg: Message):
    await msg.answer(HELP_TEXT, reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:open:help")
async def help_from_menu(cb: CallbackQuery):
    await cb.message.edit_text(HELP_TEXT, reply_markup=main_menu_kb())
    await cb.answer()
