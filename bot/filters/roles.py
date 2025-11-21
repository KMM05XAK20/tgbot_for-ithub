from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from ..config import get_settings
from ..storage.db import SessionLocal
from ..storage.models import User as UserModel

class IsAdmin(BaseFilter):
    def __init__(self):
        setting = get_settings()
        # читаем ID из .env → Settings
        self.super_admin_ids = set(setting.admin_ids or [])

    async def __call__(self, message: Message) -> bool:
        tg_id = message.from_user.id

        if tg_id in self.super_admin_ids:
            return True
        
        with SessionLocal() as s:
            user = s.query(UserModel).filter_by(tg_id=tg_id).first()
            return bool(user and user.is_admin)
