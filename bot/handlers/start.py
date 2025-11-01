from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from ..keyboards.common import welcome_kb, roles_grid_kb, main_menu_kb
from ..services.users import get_or_create_user, set_role
router = Router()

WELCOME_TEXT = (
    "👋 Привет, инфлюенсер! Добро пожаловать в INFLUENCE.HUB\n"
    "Мы очень рады, что ты решил присоединиться к нашей потрясающей активности!\n\n"
    "Нажми «Начать», чтобы выбрать роль и перейти в меню."
)

@router.message(CommandStart())
async def on_start(message: Message):
    get_or_create_user(message.from_user.id, message.from_user.username)
    await message.answer(WELCOME_TEXT, reply_markup=welcome_kb())

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
