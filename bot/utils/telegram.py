from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message


async def safe_edit_text(message: Message, text: str, **kwargs) -> None:
    """
    Безопасно редактирует текст сообщения:
    - если текст и разметка те же самые, Telegram кидает ошибку
      'message is not modified' — мы её молча игнорируем
    - все остальные ошибки пробрасываем дальше
    """
    try:
        await message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            # Просто ничего не делаем — для пользователя изменений нет
            return
        raise
