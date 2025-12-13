from unittest.mock import AsyncMock
from venv import create
import pytest

@pytest.mark.asyncio
async def test_open_tasks_root_renders_list(cb, mocker):
    from bot.handlers.task.catalog import open_tasks_root

    # мок списка задач
    t1 = type("T", (), 
              {"id": 1, 
               "title": "Задача 1", 
               "difficulty": "easy",
               "reward_coins": 5, 
               "deadline_days": 2})()
    
    mocker.patch("bot.handlers.task.catalog.list_tasks_for_catalog", return_value=[t1], create=True)

    mocker.patch("bot.handlers.task.catalog.tasks_filters_kb", return_value="KB", create=True)
    mocker.patch("bot.handlers.task.catalog.safe_edit_text", new=AsyncMock(), create=True)

    cb.data = "tasks:open"
    await open_tasks_root(cb)

    # главное: safe_edit_text вызвался
    from bot.handlers.task import catalog as mod
    mod.safe_edit_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_open_tasks_root_renders_list(cb, mocker):
    from bot.handlers.task.catalog import open_tasks_root

    t1 = type("T", (), {
        "id": 1, "title": "Задача 1", "difficulty": "easy", "reward_coins": 5, "deadline_days": 2
    })()

    mocker.patch("bot.handlers.task.catalog.list_tasks_for_catalog", return_value=[t1], create=True)
    mocker.patch("bot.handlers.task.catalog.tasks_filters_kb", return_value="KB", create=True)

    safe_edit = mocker.patch("bot.handlers.task.catalog.safe_edit_text", new=AsyncMock(), create=True)

    cb.data = "tasks:open"
    await open_tasks_root(cb)

    safe_edit.assert_awaited()
    cb.answer.assert_awaited()

@pytest.mark.asyncio
async def test_task_view_shows_take_button_if_not_taken(cb, mocker):
    from bot.handlers.task.catalog import open_task_details

    task = type("T", (), {"id": 1, "title": "X", "difficulty": "easy", "reward_coins": 5, "deadline_days": None})()
    mocker.patch("bot.handlers.task.catalog.get_task_by_id", return_value=task, create=True)
    mocker.patch("bot.handlers.task.catalog.has_active_assignment", return_value=False, create=True)

    kb = mocker.patch("bot.handlers.task.catalog.task_view_kb", return_value="KB", create=True)
    safe_edit = mocker.patch("bot.handlers.task.catalog.safe_edit_text", new=AsyncMock(), create=True)

    cb.data = "tasks:view:1"
    await open_task_details(cb)

    kb.assert_called_once_with(task_id=1, already_taken=False)
    safe_edit.assert_awaited()
