from typing import Iterable, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..storage.db import SessionLocal
from ..storage.models import Task, TaskAssignment, User
from datetime import datetime, timedelta

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
