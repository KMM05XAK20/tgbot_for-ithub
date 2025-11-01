from typing import Iterable, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from ..storage.db import SessionLocal
from ..storage.models import Task, TaskAssignment, User
from datetime import datetime, timedelta


def get_active_assignment(user_tg_id: int, task_id: int) -> TaskAssignment | None:
    with SessionLocal() as s:
        user = s.execute(select(User).where(User.tg_id == user_tg_id)).scalar_one_or_none()
        if not user:
            return None
        return s.execute(
            select(TaskAssignment).where(
                TaskAssignment.user_id == user.id,
                TaskAssignment.task_id == task_id,
                TaskAssignment.status.in_(["in_progress", "submitted"])
            ).order_by(TaskAssignment.id.desc())
        ).scalar_one_or_none()

def submit_assignment_text(assignment_id: int, text: str) -> bool:
    with SessionLocal() as s:
        a = s.get(TaskAssignment, assignment_id)
        if not a:
            return False
        a.submission_text = text
        a.submitted_at = datetime.utcnow()
        a.status = "submitted"
        s.commit()
        return True

def submit_assignment_file(assignment_id: int, file_id: str) -> bool:
    with SessionLocal() as s:
        a = s.get(TaskAssignment, assignment_id)
        if not a:
            return False
        a.submission_file_id = file_id
        a.submitted_at = datetime.utcnow()
        a.status = "submitted"
        s.commit()
        return True

def seed_tasks_if_empty() -> int:
    """Наполнить каталог тестовыми задачами один раз."""
    with SessionLocal() as s:
        count = s.scalar(select(func.count(Task.id)))
        if count and count > 0:
            return 0
        data = [
            Task(title="Репост события", description="Поделись анонсом в соцсетях", difficulty="easy", reward_coins=3, deadline_hours=24),
            Task(title="Участие в опросе", description="Ответь на 5 вопросов", difficulty="easy", reward_coins=2, deadline_hours=24),
            Task(title="Написать пост для блога", description="Пост 1500+ знаков", difficulty="medium", reward_coins=8, deadline_hours=48),
            Task(title="Снять короткий обзор", description="Видео до 60 секунд", difficulty="medium", reward_coins=10, deadline_hours=72),
            Task(title="Организовать митап", description="Подготовка и проведение", difficulty="hard", reward_coins=15, deadline_hours=168),
        ]
        s.add_all(data)
        s.commit()
        return len(data)

def list_tasks(difficulty: Optional[str], page: int = 1, per_page: int = 5) -> list[Task]:
    with SessionLocal() as s:
        stmt = select(Task).where(Task.status == "active")
        if difficulty in {"easy", "medium", "hard"}:
            stmt = stmt.where(Task.difficulty == difficulty)
        stmt = stmt.order_by(Task.id.desc()).limit(per_page).offset((page - 1) * per_page)
        return list(s.scalars(stmt))

def get_task(task_id: int) -> Optional[Task]:
    with SessionLocal() as s:
        return s.get(Task, task_id)

def has_active_assignment(user_tg_id: int, task_id: int) -> bool:
    with SessionLocal() as s:
        user = s.execute(select(User).where(User.tg_id == user_tg_id)).scalar_one_or_none()
        if not user:
            return False
        exists = s.execute(
            select(func.count(TaskAssignment.id)).where(
                TaskAssignment.user_id == user.id,
                TaskAssignment.task_id == task_id,
                TaskAssignment.status.in_(["in_progress", "submitted"])
            )
        ).scalar_one()
        return exists > 0

def take_task(user_tg_id: int, task_id: int) -> bool:
    """Вернёт True если удалось взять; False если уже было взято."""
    with SessionLocal() as s:
        user = s.execute(select(User).where(User.tg_id == user_tg_id)).scalar_one_or_none()
        task = s.get(Task, task_id)
        if not user or not task:
            return False
        # запретим дубли
        dup = s.execute(
            select(TaskAssignment).where(
                TaskAssignment.user_id == user.id,
                TaskAssignment.task_id == task_id,
                TaskAssignment.status.in_(["in_progress", "submitted"])
            )
        ).scalar_one_or_none()
        if dup:
            return False
        due = datetime.utcnow() + timedelta(hours=task.deadline_hours or 48)
        s.add(TaskAssignment(task_id=task.id, user_id=user.id, due_at=due))
        s.commit()
        return True

def _resolve_user(s: SessionLocal, user_tg_id: int) -> User | None:
    return s.execute(select(User).where(User.tg_id == user_tg_id)).scalar_one_or_none()

def count_assignments_by_status(user_tg_id: int) -> dict[str, int]:
    """Вернёт агрегаты по группам статусов: active / submitted / done"""
    with SessionLocal() as s:
        user = _resolve_user(s, user_tg_id)
        if not user:
            return {"active": 0, "submitted": 0, "done": 0}
        q = select(TaskAssignment.status, func.count(TaskAssignment.id))\
            .where(TaskAssignment.user_id == user.id)\
            .group_by(TaskAssignment.status)
        rows = s.execute(q).all()
        by_status = {st: cnt for st, cnt in rows}
        active = by_status.get("in_progress", 0)
        submitted = by_status.get("submitted", 0)
        done = by_status.get("approved", 0) + by_status.get("rejected", 0)
        return {"active": active, "submitted": submitted, "done": done}

def list_assignments(user_tg_id: int, group: str, page: int = 1, per_page: int = 5) -> list[tuple]:
    """
    Возвращает список элементов:
    (assignment_id, task_title, status, due_at, submitted_at)
    group: 'active' | 'submitted' | 'done'
    """
    group_map = {
        "active": ["in_progress"],
        "submitted": ["submitted"],
        "done": ["approved", "rejected"],
    }
    statuses = group_map.get(group, ["in_progress"])
    with SessionLocal() as s:
        user = _resolve_user(s, user_tg_id)
        if not user:
            return []
        stmt = (
            select(
                TaskAssignment.id,
                Task.title,
                TaskAssignment.status,
                TaskAssignment.due_at,
                TaskAssignment.submitted_at,
            )
            .join(Task, Task.id == TaskAssignment.task_id)
            .where(TaskAssignment.user_id == user.id, TaskAssignment.status.in_(statuses))
            .order_by(TaskAssignment.id.desc())
            .limit(per_page)
            .offset((page - 1) * per_page)
        )
        return list(s.execute(stmt).all())
