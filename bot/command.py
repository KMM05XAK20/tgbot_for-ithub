from aiogram import Bot
from aiogram.types import BotCommand


async def setup_bot_commands(bot: Bot) -> None:
    """
    Регистрируем список команд, который виден в меню Телеграма.
    """
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="menu", description="Открыть главное меню"),
        BotCommand(command="help", description="Справка и контакты"),
        BotCommand(command="whoime", description="Мой профиль / кто я"),
        # ниже — по желанию, если реально пользуешься:
        BotCommand(command="admin", description="Админ-панель (для админов)"),
    ]

    await bot.set_my_commands(commands)
    print("[setup_bot_commands] Bot commands set")