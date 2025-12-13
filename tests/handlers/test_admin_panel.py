import pytest


@pytest.mark.asyncio
async def test_admin_entry_shows_panel(msg, mocker):
    from bot.handlers.admin.panel import admin_entry

    # патчим клавиатуру, чтобы не зависеть от InlineKeyboardMarkup
    mocker.patch(
        "bot.handlers.admin.panel.admin_panel_kb", return_value="KB", create=True
    )

    await admin_entry(msg)

    msg.message.answer.assert_awaited_once()
    args, kwargs = msg.message.answer.call_args
    assert "Админ-панель" in args[0]
    assert kwargs["reply_markup"] == "KB"
