import pytest
from unittest.mock import AsyncMock

from tests.conftest import state

@pytest.mark.asyncio
async def test_submit_start_no_assignment_shows_alert(cb, mocker):
    from bot.handlers.task.submission import submit_start

    mocker.patch("bot.handlers.task.submission.get_active_assignment", return_value=None)

    # safe_edit_text/answer могут быть внутри, поэтому подстрахуем
    cb.answer = AsyncMock()

    cb.data = "tasks:submit:1"
    await submit_start(cb, state)

    # ожидаем, что будет хотя бы cb.answer (alert/notify)
    cb.answer.assert_awaited()
