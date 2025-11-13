from typing import Iterable, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from .users import get_user
from ..storage.db import SessionLocal
from ..storage.models import Task, TaskAssignment, User
from datetime import datetime, timedelta


def admin_list_all_tasks() -> list[Task]:
    with SessionLocal as s:
        return s.query(Task).order_by(Task.id.desc()).all()


def admin_toggle_task_published(task_id: int) -> bool:
    with SessionLocal() as s:
        t = s.query(Task).filter(Task.id == task_id).first()
        if not t:
            return False
        t.published = not bool(getattr(t, "published", False))
        s.commit()
        return True

def admin_delete_task(task_id: int) -> bool:
    with SessionLocal() as s:
        t = s.query(Task).filter(Task.id == task_id).first()
        if not t:
            return False
        s.delete(t)
        s.commit()
        return True


def admin_create_task(*, title: str, description: str, reward: int, difficulty: str, deadline_days: int) -> int:
    """difficulty: easy|medium|hard; deadline_days >= 0"""
    with SessionLocal() as s:
        t = Task(
            title=title,
            description=description,
            reward=reward,
            difficulty=difficulty,
            published=False,
            created_at=datetime.utcnow(),
            deadline_days=deadline_days,
        )
        s.add(t)
        s.commit()
        s.refresh(t)
        return t.id

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



def _task_field_map() -> dict[str, str | None]:
    title = "title" if hasattr(Task, "title") else None
    description = "description" if hasattr(Task, "description") else None
    reward = "reward" if hasattr(Task, "reward") else ("coins" if hasattr(Task, "coins") else None)
    difficulty = "difficulty" if hasattr(Task, "difficulty") else ("level" if hasattr(Task, "level") else None)
    published = "published" if hasattr(Task, "published") else ("is_published" if hasattr(Task, "is_published") else None)
    deadline_days = "deadline_days" if hasattr(Task, "deadline_days") else ("deadline" if hasattr(Task, "deadline") else None)
    created_at = "created_at" if hasattr(Task, "created_at") else None
    return {
        "title": title,
        "description": description,
        "reward": reward,
        "difficulty": difficulty,
        "published": published,
        "deadline_days": deadline_days,
        "created_at": created_at,
    }


def _create_task_obj(*, title: str, description: str, reward: int, difficulty: str, deadline_days: int) -> Task:
    fm = _task_field_map()
    t = Task()  # ВАЖНО: без kwargs!

    if fm["title"]:          setattr(t, fm["title"], title)
    if fm["description"]:    setattr(t, fm["description"], description)
    if fm["reward"]:         setattr(t, fm["reward"], reward)
    if fm["difficulty"]:     setattr(t, fm["difficulty"], difficulty)
    if fm["published"]:      setattr(t, fm["published"], False)
    if fm["deadline_days"]:  setattr(t, fm["deadline_days"], deadline_days)
    if fm["created_at"]:     setattr(t, fm["created_at"], datetime.utcnow())

    return t


def admin_create_task(*, title: str, description: str, reward: int, difficulty: str, deadline_days: int) -> int:
    with SessionLocal() as s:
        t = _create_task_obj(
            title=title,
            description=description,
            reward=reward,
            difficulty=difficulty,
            deadline_days=deadline_days,
        )
        s.add(t)
        s.commit()
        s.refresh(t)
        return t.id


def seed_tasks_if_empty() -> None:
    with SessionLocal() as s:
        count = s.query(Task).count()
        if count > 0:
            return
        samples = [
            dict(title="Репост события", description="Сделай репост анонса", reward=3, difficulty="easy",   deadline_days=2),
            dict(title="Пост в блог",    description="Напиши короткий пост",  reward=8, difficulty="medium", deadline_days=3),
            dict(title="Организуй митап",description="Подготовь офлайн-встречу", reward=13, difficulty="hard", deadline_days=7),
        ]
        for d in samples:
            s.add(_create_task_obj(**d))
        s.commit()

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


def list_pending_submissions(page: int = 1, per_page: int = 10):
    """
    Возвращает список pending заявок:
    (assignment_id, task_title, user_tg_id, username, submitted_at)
    """
    with SessionLocal() as s:
        stmt = (
            select(
                TaskAssignment.id,
                Task.title,
                User.tg_id,
                User.username,
                TaskAssignment.submitted_at,
            )
            .join(Task, Task.id == TaskAssignment.task_id)
            .join(User, User.id == TaskAssignment.user_id)
            .where(TaskAssignment.status == "submitted")
            .order_by(TaskAssignment.submitted_at.desc())
            .limit(per_page)
            .offset((page - 1) * per_page)
        )
        return list(s.execute(stmt).all())

def get_assignment_full(assignment_id: int):
    """Вернёт assignment + связанные task/user."""
    with SessionLocal() as s:
        a = s.query(TaskAssignment)\
            .options(joinedload(TaskAssignment.task), joinedload(TaskAssignment.user))\
            .get(assignment_id)
        return a

def approve_assignment(assignment_id: int) -> bool:
    with SessionLocal() as s:
        a = s.get(TaskAssignment, assignment_id)
        if not a or a.status not in ("submitted", "in_progress"):
            return False
        t = s.get(Task, a.task_id)
        u = s.get(User, a.user_id)
        a.status = "approved"
        # начислить монеты
        u.coins = (u.coins or 0) + (t.reward_coins or 0)
        s.commit()
        return True

def reject_assignment(assignment_id: int) -> bool:
    with SessionLocal() as s:
        a = s.get(TaskAssignment, assignment_id)
        if not a or a.status not in ("submitted", "in_progress"):
            return False
        a.status = "rejected"
        s.commit()
        return True
    
def count_assignments_by_status(user_tg_id: int) -> dict[str, int]:
    """
    Возвращает количество по группам: active/submitted/done
    active = in_progress; submitted = submitted; done = approved|rejected
    """
    with SessionLocal() as s:
        u = s.execute(select(User).where(User.tg_id == user_tg_id)).scalar_one_or_none()
        if not u:
            return {"active": 0, "submitted": 0, "done": 0}

        base = select(TaskAssignment.status, func.count()).where(TaskAssignment.user_id == u.id).group_by(TaskAssignment.status)
        rows = s.execute(base).all()
        raw = {st: cnt for st, cnt in rows}
        active = raw.get("in_progress", 0)
        submitted = raw.get("submitted", 0)
        done = raw.get("approved", 0) + raw.get("rejected", 0)
        return {"active": active, "submitted": submitted, "done": done}

def list_assignments(user_tg_id: int, group: str, page: int = 1, per_page: int = 10, diff: str = "all"):
    """
    -> [(assignment_id, title, status, reward, due_at, submitted_at)]
    """
    with SessionLocal() as s:
        u = s.execute(select(User).where(User.tg_id == user_tg_id)).scalar_one_or_none()
        if not u:
            return []

        if group == "active":
            cond_group = TaskAssignment.status == "in_progress"
        elif group == "submitted":
            cond_group = TaskAssignment.status == "submitted"
        else:
            cond_group = or_(TaskAssignment.status == "approved", TaskAssignment.status == "rejected")

        stmt = (
            select(
                TaskAssignment.id,
                Task.title,
                TaskAssignment.status,
                Task.reward_coins,
                TaskAssignment.due_at,
                TaskAssignment.submitted_at,
            )
            .join(Task, Task.id == TaskAssignment.task_id)
            .where(TaskAssignment.user_id == u.id)
            .where(cond_group)
        )

        cond_diff = difficulty_condition(diff)
        if cond_diff is not None:
            stmt = stmt.where(cond_diff)
        # ✅ корректная сортировка без updated_at
        if group == "active":
            # ближайшие дедлайны сверху; пустые дедлайны — внизу
            stmt = stmt.order_by(
                TaskAssignment.due_at.asc().nullslast(),
                TaskAssignment.id.desc(),
            )
        else:
            # свежеприсланные сверху; если submitted_at пуст — внизу
            stmt = stmt.order_by(
                TaskAssignment.submitted_at.desc().nullslast(),
                TaskAssignment.id.desc(),
            )


def get_assignment_card(assignment_id: int):
    """
    Полная карточка для просмотра.
    -> dict | None
    """
    with SessionLocal() as s:
        a = s.get(TaskAssignment, assignment_id)
        if not a:
            return None
        t = s.get(Task, a.task_id)
        u = s.get(User, a.user_id)
        return {
            "id": a.id,
            "status": a.status,
            "due_at": a.due_at,
            "submitted_at": a.submitted_at,
            "submission_text": a.submission_text,
            "has_file": bool(a.submission_file_id),
            "task_title": t.title if t else "—",
            "reward": t.reward_coins if t else 0,
            "user_tg_id": u.tg_id if u else None,
        }

def reward_to_difficulty(reward: int | None) -> str:
    """
    Маппинг сложности по монетам.
    🟢 easy:   <=5
    🟡 medium: 6..10
    🔴 hard:   >10
    """
    r = int(reward or 0)
    if r <= 5:
        return "easy"
    if r <= 10:
        return "medium"
    return "hard"

def difficulty_condition(diff: str):
    """
    Возвращает SQL-условие по Task.reward_coins для сложностей easy/medium/hard.
    """
    diff = (diff or "all").lower()
    if diff == "easy":
        return Task.reward_coins <= 5
    if diff == "medium":
        return and_(Task.reward_coins >= 6, Task.reward_coins <= 10)
    if diff == "hard":
        return Task.reward_coins > 10
    return None  # all
