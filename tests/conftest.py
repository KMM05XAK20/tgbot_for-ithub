from types import SimpleNamespace
import pytest
from unittest.mock import AsyncMock


class FakeUser(SimpleNamespace):
    pass


@pytest.fixture
def msg():
    # имитируем aiogram Message минимально
    return SimpleNamespace(
        text="",
        answer=AsyncMock(),
        edit_text=AsyncMock(),
        from_user=FakeUser(id=111, username="tester"),
        chat=SimpleNamespace(id=222),
        bot=SimpleNamespace(send_message=AsyncMock()),
    )


@pytest.fixture
def cb():
    # имитируем CallbackQuery минимально
    m = SimpleNamespace(
        text="",
        chat=SimpleNamespace(id=222),
        edit_text=AsyncMock(),
    )
    return SimpleNamespace(
        data="",
        from_user=SimpleNamespace(id=111, username="tester"),
        message=m,
        answer=AsyncMock(),
    )


@pytest.fixture
def state():
    return SimpleNamespace(
        clear=AsyncMock(),
        set_state=AsyncMock(),
        update_data=AsyncMock(),
        get_data=AsyncMock(return_value={}),
    )
