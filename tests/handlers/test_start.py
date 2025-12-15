import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_start_shows_welcome_and_menu(msg, mocker):
    # импорт внутри теста (важно для корректных patch)
    from bot.handlers.start import cmd_start

    # если в старте создаётся/обновляется пользователь
    mocker.patch("bot.handlers.start.upsert_user", create=True)

    # если строится клавиатура
    mocker.patch("bot.handlers.start.main_menu_kb", return_value="KB", create=True)

    await cmd_start(msg)

    msg.answer.assert_awaited_once()
