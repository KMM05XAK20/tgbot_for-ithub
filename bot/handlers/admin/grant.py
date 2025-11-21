
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ...config import get_settings
from ...services.users import set_admin_status

router = Router(name="admin_grant")


@router.message(Command("add_admin"))
async def add_admin_by_reply(msg: Message):
    """
    Команда: /add_admin
    Использование: ответить этой командой на сообщение пользователя.
    Работает только для супер-админов из ADMIN_IDS.
    """
    settings = get_settings()
    super_admins = set(settings.admin_ids or [])

    # 1. Проверяем, что вызывающий - супер-админ
    if msg.from_user.id not in super_admins:
        await msg.answer("❌ У тебя нет прав назначать админов.")
        return

    # 2. Проверяем, что команда отправлена ответом на сообщение
    if not msg.reply_to_message or not msg.reply_to_message.from_user:
        await msg.answer("Использование: ответь на сообщение пользователя командой /add_admin.")
        return

    target = msg.reply_to_message.from_user
    target_tg_id = target.id

    # 3. Пробуем выдать админку
    ok = set_admin_status(target_tg_id, True)
    if not ok:
        await msg.answer(
            "❌ Пользователь не найден в базе.\n"
            "Попроси его сначала написать боту /start, а потом повтори /add_admin."
        )
        return

    mention = f"@{target.username}" if target.username else str(target_tg_id)

    # 4. Подтверждение тебе
    await msg.answer(f"✅ Пользователь {mention} теперь администратор.")

    # 5. Уведомление самому пользователю (если хочешь)
    try:
        await msg.bot.send_message(
            target_tg_id,
            "🛡 Тебе выдали права администратора в боте INFLUENCE.HUB."
        )
    except Exception:
        # Если пользователь запретил ЛС — просто молча игнорируем
        pass
