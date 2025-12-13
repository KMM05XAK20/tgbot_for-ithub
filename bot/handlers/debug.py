# bot/handlers/debug.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..services.users import get_user  # или get_or_create_user, как у тебя
from ..config import get_settings

router = Router(name="debug")


@router.message(Command("whoime"))
async def whoime(msg: Message):
    user = get_user(msg.from_user.id)
    setting = get_settings()

    db_admin = bool(user and getattr(user, "is_admin", False))

    super_admin = msg.from_user.id in set(setting.admin_ids or [])
    is_admin = super_admin or db_admin

    role = getattr(user, "role", None) if user else None
    coins = getattr(user, "coins", 0) if user else 0

    if super_admin:
        admin_text = "супер-админ"
    elif db_admin:
        admin_text = "админ"
    else:
        admin_text = "нет админки"

    text = (
        f"🆔 <b>{msg.from_user.id}</b>\n"
        f"👤 @{msg.from_user.username or '—'}\n"
        f"🎭 Роль: <b>{role or '—'}</b>\n"
        f"🪙 Coins: <b>{coins}</b>\n"
        f"🛡 Админ: <b>{admin_text}</b>"
    )
    await msg.answer(text)
