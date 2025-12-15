import re
from tkinter import N, NO
from unittest import mock
from aiogram import F
import pytest
from types import SimpleNamespace
from bot.services import tasks as svc

def test_approve_adds_coins(mocker):


    assignment = SimpleNamespace(id=10, 
                                 task_id=2, 
                                 user_id=1, 
                                 status="submitted")
    task = SimpleNamespace(id=2, 
                           reward_coins=7)
    user = SimpleNamespace(id=1, 
                           tg_id=777,
                           coins=0)

    class FakeSession:
        def __init__(self):
            self.commit_called = False

        def get(self, model, pk):
            if pk == 10:
                return assignment
            if pk == 1:
                return user
            if pk == 2:
                return task
            return None        

        def commit(self):
            self.commit_called = True

        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc, tb):
            return False
        
    fake_session = FakeSession()

    mocker.patch("bot.services.tasks.SessionLocal", return_value=fake_session)

    # mocker.patch.object(
    #     svc, "bot.services.tasks.get_assignment_by_id", return_value=assignment, create=True
    # )
    # mocker.patch.object(svc, "bot.services.tasks.get_task_by_id", return_value=task, create=True)
    # mocker.patch.object(svc, "bot.services.tasks.get_user_by_id", return_value=user, create=True)

    # # мок “сохранения”
    # mocker.patch("bot.services.tasks._commit", create=True)
    # # mocker.patch.object(svc, "_commit", create=True)

    ok = svc.approve_assignment(assignment_id=10)
    assert ok is True
    assert assignment.status == "approved"
    assert user.coins == 7
    assert fake_session.commit_called is True

def test_approve_returns_false_if_not_found(mocker):

    class FakeSession:
        def get(self, model, pk):
            return None  # ничего не нашли
        def commit(self):
            raise AssertionError("commit should not be called")
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False

    mocker.patch("bot.services.tasks.SessionLocal", return_value=FakeSession())

    assert svc.approve_assignment(999) is False


def test_approve_returns_false_if_wrong_status(mocker):

    assignment = SimpleNamespace(id=10, task_id=2, user_id=1, status="approved")

    class FakeSession:
        def get(self, model, pk):
            return assignment if pk == 10 else None
        def commit(self):
            raise AssertionError("commit should not be called")
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False

    mocker.patch("bot.services.tasks.SessionLocal", return_value=FakeSession())

    assert svc.approve_assignment(10) is False
