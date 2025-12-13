from venv import create
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_take_task_when_no_active_assignment(cb, mocker):
    from bot.handlers.task.catalog import open_task_details

    mocker.patch.object(cb, "_commit", create=True)
    mocker.patch("bot.handlers.task.catalog.has_active_assignment", return_value=False, create=True)
    take = mocker.patch("bot.handlers.task.catalog.take_task", return_value=True, create=True)
    safe_edit = mocker.patch("bot.handlers.task.catalog.safe_edit_text", new=AsyncMock(), create=True)
    kb = mocker.patch("bot.handlers.task.catalog.task_view_kb", return_value="KB", create=True)

    cb.data = "tasks:take:2"
    await open_task_details(cb)

    take.assert_called_once()
    kb.assert_called_once_with(task_id=2, already_taken=True)
    safe_edit.assert_awaited()
    cb.answer.assert_awaited()

@pytest.mark.asyncio
async def test_take_task_when_already_taken_shows_alert(cb, mocker):
    from bot.handlers.task.catalog import open_task_details

    mocker.patch("bot.handlers.task.catalog.has_active_assignment", return_value=True, create=True)

    cb.data = "tasks:take:2"
    await open_task_details(cb)

    cb.answer.assert_awaited()  # обычно show_alert=True внутри
