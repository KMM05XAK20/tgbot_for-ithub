import pytest
from types import SimpleNamespace

@pytest.mark.asyncio
async def test_menu_root_renders(cb, mocker):
    from bot.handlers.menu import open_main_menu

    mocker.patch("bot.handlers.menu.main_menu_kb", return_value="KB", create=True)

    await open_main_menu(cb)

    cb.answer.assert_awaited_once()
