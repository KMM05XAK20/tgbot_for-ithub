from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, InlineKeyboardMarkup


async def safe_edit_text(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    **kwargs,
):
    """
    Безопасно правим текст сообщения:
    - игнорируем ошибку 'message is not modified'
    - остальные пробрасываем наверх
    """
    with suppress(TelegramBadRequest) as ctx:
        await message.edit_text(text, reply_markup=reply_markup, **kwargs)

    # если это был не 'message is not modified' — перекинем ошибку
    if ctx.token is not None:
        err = ctx.token
        if "message is not modified" not in str(err):
            raise err
