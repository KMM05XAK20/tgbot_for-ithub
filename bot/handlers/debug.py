# bot/handlers/debug.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..services.users import get_user  # или get_or_create_user, как у тебя

router = Router(name="debug")


@router.message(Command("whoime"))
async def whoime(msg: Message):
    user = get_user(msg.from_user.id)

    role = getattr(user, "role", None) if user else None
    coins = getattr(user, "coins", 0) if user else 0
    is_admin = getattr(user, "is_admin", False) if user else False

    text = (
        f"🆔 <b>{msg.from_user.id}</b>\n"
        f"👤 @{msg.from_user.username or '—'}\n"
        f"🎭 Роль: <b>{role or '—'}</b>\n"
        f"🪙 Coins: <b>{coins}</b>\n"
        f"🛡 Админ: <b>{'да' if is_admin else 'нет'}</b>"
    )
    await msg.answer(text)
