import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_broadcast_send_ok(mocker):
    from bot.handlers.admin.broadcast import broadcast_send

    # callback-query mock
    cb = SimpleNamespace()
    cb.from_user = SimpleNamespace(id=111, username="tester")

    # сообщение, к которому "прикреплён" callback
    cb.message = SimpleNamespace()
    cb.message.edit_text = AsyncMock()
    cb.message.answer = AsyncMock()

    # bot
    cb.bot = SimpleNamespace()
    cb.bot.send_message = AsyncMock()

    # cb.answer()
    cb.answer = AsyncMock()

    # патчим выборку пользователей (в модуле хендлера!)
    mocker.patch(
        "bot.handlers.admin.broadcast.get_all_user_tg_ids",
        return_value=[1, 2, 3],
    )

    # state
    state = SimpleNamespace()
    state.get_data = AsyncMock(return_value={"text": "Привет всем!"})
    state.clear = AsyncMock()

    # ВАЖНО: вызываем с cb, а не msg
    await broadcast_send(cb, state, cb.bot)

    assert cb.bot.send_message.await_count == 3
    state.clear.assert_awaited_once()
