import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_admin_events_root_no_events(mocker, cb):
    # важно патчить В МОДУЛЕ ХЕНДЛЕРА, а не в services.events
    mocker.patch("bot.handlers.admin.events.list_upcoming_events", return_value=[])
    mocker.patch("bot.handlers.admin.events.admin_events_kb", return_value="KB")

    from bot.handlers.admin.events import admin_events_root

    cb.data = "admin:events"
    await admin_events_root(cb)

    cb.message.edit_text.assert_awaited_once()
    cb.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_events_root_with_events(mocker, cb):
    ev = mocker.MagicMock()
    ev.title = "Событие 1"
    ev.event_date = datetime(2025, 12, 12, 18, 0)

    mocker.patch("bot.handlers.admin.events.list_upcoming_events", return_value=[ev])
    mocker.patch("bot.handlers.admin.events.admin_events_kb", return_value="KB")

    from bot.handlers.admin.events import admin_events_root

    await admin_events_root(cb)

    args, kwargs = cb.message.edit_text.await_args
    text = args[0]
    assert "Событие 1" in text
    assert "2025-12-12 18:00" in text
    cb.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_events_add_start(mocker, cb, state):
    from bot.handlers.admin.events import admin_events_add_start
    from bot.states.events import AdminEventForm

    await admin_events_add_start(cb, state)

    state.clear.assert_awaited_once()
    state.set_state.assert_awaited_once_with(AdminEventForm.waiting_title)
    cb.message.edit_text.assert_awaited_once()
    cb.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_event_title_ok(msg, state):
    from bot.handlers.admin.events import admin_event_title
    from bot.states.events import AdminEventForm

    msg.text = "  Митап  "
    await admin_event_title(msg, state)

    state.update_data.assert_awaited_once_with(title="Митап")
    msg.answer.assert_awaited_once()
    state.set_state.assert_awaited_once_with(AdminEventForm.waiting_description)


@pytest.mark.asyncio
async def test_admin_event_date_invalid(msg, state):
    from bot.handlers.admin.events import admin_event_date

    msg.text = "2025-12-32"
    await admin_event_date(msg, state)

    msg.answer.assert_awaited_once()
    state.update_data.assert_not_called()


@pytest.mark.asyncio
async def test_admin_event_time_valid(mocker, msg, state):
    from bot.handlers.admin.events import admin_event_time
    from bot.keyboards.common import admin_events_kb

    # данные FSM
    state.get_data.return_value = {
        "title": "Митап",
        "description": "описание",
        "date": "2025-12-24",
    }

    create_event_mock = mocker.patch("bot.handlers.admin.events.create_event")
    kb_mock = mocker.patch("bot.handlers.admin.events.admin_events_kb", return_value=admin_events_kb())

    msg.text = "18:30"
    msg.from_user.id = 777

    await admin_event_time(msg, state)

    create_event_mock.assert_called_once()
    kwargs = create_event_mock.call_args.kwargs
    assert kwargs["title"] == "Митап"
    assert kwargs["description"] == "описание"
    assert kwargs["event_dt"] == datetime(2025, 12, 24, 18, 30)
    assert kwargs["creator_tg_id"] == 777

    state.clear.assert_awaited_once()
    msg.answer.assert_awaited_once()
