import pytest
from unittest.mock import AsyncMock

from tests.conftest import state


@pytest.mark.asyncio
async def test_submit_start_no_assignment_shows_alert(cb, mocker):
    from bot.handlers.task.submission import submit_start

    mocker.patch(
        "bot.handlers.task.submission.get_active_assignment", return_value=None
    )

    # safe_edit_text/answer могут быть внутри, поэтому подстрахуем
    cb.answer = AsyncMock()

    cb.data = "tasks:submit:1"
    await submit_start(cb, state)

    # ожидаем, что будет хотя бы cb.answer (alert/notify)
    cb.answer.assert_awaited()


@pytest.mark.asyncio
async def test_submit_start_ok_sets_state(cb, state, mocker):
    from bot.handlers.task.submission import submit_start
    from bot.states.task_submit import TaskSubmit

    assignment = type("A", (), {"id": 10, "task_id": 1})()
    mocker.patch("bot.handlers.task.submission.get_active_assignment", return_value=assignment)

    cb.data = "tasks:submit:1"
    await submit_start(cb, state)

    state.update_data.assert_awaited()  # сохраняем assignment/task_id
    state.set_state.assert_awaited_once_with(TaskSubmit.waiting_proof)
    cb.message.edit_text.assert_awaited()  # просим прислать текст/ссылку