from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from ..keyboards.common import welcome_kb, roles_grid_kb, main_menu_kb
from ..services.users import get_or_create_user, set_role

router = Router(name="start")

# WELCOME_TEXT = (
#     "👋 Привет, инфлюенсер! Добро пожаловать в INFLUENCE.HUB\n"
#     "Мы очень рады, что ты решил присоединиться к нашей потрясающей активности!\n\n"
#     "Нажми «Начать», чтобы выбрать роль и перейти в меню."
# )

@router.message(Command("start"))
async def cmd_start(msg: Message):


    text = (
        "👋 Привет!\n\n"
        "<b>INFLUENCE.HUB</b> — это бот-хаб для участников сообщества:\n"
        "• выполняй задания и копи 🪙 coins\n"
        "• поднимай уровень и получай бейджи 🏅\n"
        "• находи наставников 👨‍🏫\n"
        "• следи за событиями в календаре 📅\n\n"
        f"Твой профиль уже создан, {('@' + msg.from_user.username) if msg.from_user.username else 'друг'}.\n"
        "Нажми кнопку ниже, чтобы открыть главное меню 👇"
    )

    await msg.answer(text, reply_markup=main_menu_kb())

@router.message(Command("whoami"))
async def whoami(msg: Message):
    await msg.answer(f"Ваш Telegram ID: <code>{msg.from_user.id}</code>")

# @router.message(CommandStart())
# async def on_start(message: Message):
#     get_or_create_user(message.from_user.id, message.from_user.username)
#     await message.answer(WELCOME_TEXT, reply_markup=welcome_kb())

@router.callback_query(F.data.startswith("role:open"))
async def on_role_choose(cb: CallbackQuery):
    role = cb.data.split(":")[-1]
    titles = {"active": "Активный спикер", "guru": "Гуру тех.заданий", "helper": "Помогатор"}
    title = titles.get(role, role)

    set_role(cb.from_user.id, role)

    await cb.message.edit_text(
        f"✅ Роль установлена: <b>{title}</b>\nОткрываю главное меню…",
        reply_markup=main_menu_kb()
    )
    await cb.answer()
