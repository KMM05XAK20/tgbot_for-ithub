def test_approve_adds_coins(mocker):
    from bot.services import tasks as svc

    # мок assignment + task + user
    assignment = type("A", (), {"id": 10, "task_id": 2, "user_id": 1, "status": "submitted"})()
    task = type("T", (), {"id": 2, "reward_coins": 7})()
    user = type("U", (), {"id": 1, "coins": 0})()

    mocker.patch.object(svc, "get_assignment_by_id", return_value=assignment, create=True)
    mocker.patch.object(svc, "get_task_by_id", return_value=task, create=True)
    mocker.patch.object(svc, "get_user_by_id", return_value=user, create=True)

    # мок “сохранения”
    mocker.patch("bot.services.tasks._commit", create=True)
    #mocker.patch.object(svc, "_commit", create=True)

    ok = svc.approve_assignment(assignment_id=10)
    assert ok is True
    assert assignment.status == "approved"
    assert user.coins == 7
