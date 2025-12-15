import pytest
from unittest.mock import AsyncMock



@pytest.mark.asyncio
async def test_take_task_when_no_active_assignment(cb, mocker):
    from bot.handlers.task.catalog import take_task_cb

    mocker.patch("bot.handlers.task.catalog.has_active_assignment", return_value=False, create=True)
    take_mock = mocker.patch("bot.handlers.task.catalog.take_task", return_value=True, create=True)

    safe_edit = mocker.patch("bot.handlers.task.catalog.safe_edit_text", new=AsyncMock(), create=True)
    cb.message.edit_text = AsyncMock()
    cb.answer = AsyncMock()

    cb.data = "tasks:take:2"
    await take_task_cb(cb)

    take_mock.assert_called_once()

    # хендлер обязан либо отредактировать сообщение, либо ответить callback'ом
    assert (safe_edit.await_count + cb.message.edit_text.await_count + cb.answer.await_count) >= 1


@pytest.mark.asyncio
async def test_take_task_when_already_taken_shows_alert(cb, mocker):
    from bot.handlers.task.catalog import take_task_cb

    mocker.patch(
        "bot.handlers.task.catalog.has_active_assignment",
        return_value=True,
        create=True,
    )

    cb.data = "tasks:take:2"
    await take_task_cb(cb)

    cb.answer.assert_awaited()  # обычно show_alert=True внутри



@pytest.mark.asyncio
async def test_take_task_when_has_active_assignment(cb, mocker):
    from bot.handlers.task.catalog import take_task_cb

    mocker.patch("bot.handlers.task.catalog.has_active_assignment", return_value=True)
    take = mocker.patch("bot.handlers.task.catalog.take_task", return_value=False)
    mocker.patch("bot.handlers.task.catalog.safe_edit_text", new=AsyncMock())

    cb.data = "tasks:take:2"
    await take_task_cb(cb)

    take.assert_not_called()
    cb.answer.assert_awaited()  # alert “у тебя уже есть активное”