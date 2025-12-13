import pytest

def test_submit_task_no_active_assignment(mocker):
    from bot.services import tasks as svc

    mocker.patch.object(svc, "get_active_assignment", return_value=None)

    ok = svc.submit_task(user_tg_id=111, task_id=1, text="hi", file_id=None)
    assert ok is False
