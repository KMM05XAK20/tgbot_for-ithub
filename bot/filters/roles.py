from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from ..config import get_settings

class IsAdmin(BaseFilter):
    def __init__(self):
        # читаем ID из .env → Settings
        self.admin_ids = set(get_settings().admin_ids)

    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        uid = getattr(obj, "from_user", None).id if hasattr(obj, "from_user") else None
        return uid in self.admin_ids