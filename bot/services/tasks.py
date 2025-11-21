from typing import Iterable, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from .users import get_user
from ..storage.db import SessionLocal
from ..storage.models import Task, TaskAssignment, User
from datetime import datetime, timedelta


def admin_create_task(*, title: str, description: str, reward: int, difficulty: str, deadline_days: int) -> int:
    """difficulty: easy|medium|hard; deadline_days >= 0"""
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

def admin_delete_task(task_id: int) -> bool:
    with SessionLocal() as s:
        t = s.query(Task).filter(Task.id == task_id).first()
        if not t:
            return False
        s.delete(t)
        s.commit()
        return True


def admin_list_all_tasks():
    with SessionLocal() as s:
        return s.query(Task).order_by(Task.id.desc()).all()

def admin_toggle_task_publised(task_id: int) -> bool:
    fm =  _task_field_map()
    pub_f = fm.get("published")
    if not pub_f:
        return False
    with SessionLocal() as s:
        t = s.query(Task).filter(Task.id == task_id).first()
        if not t:
            return False
        setattr(t, pub_f, not bool(getattr(t, pub_f)))
        s.commit()
        return True

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


def list_tasks(*, min_reward: int | None = None, max_reward: int | None = None,
               difficulty: str | None = None, only_published: bool = True):
    fm = _task_field_map()
    with SessionLocal() as s:
        q = s.query(Task)
        pub_f = fm.get("published")
        rew_f = fm.get("reward")
        dif_f = fm.get("difficulty")
        if only_published and pub_f:
            q = q.filter(getattr(Task, pub_f) == True)  # noqa: E712
        if difficulty and dif_f:
            q = q.filter(getattr(Task, dif_f) == difficulty)
        if rew_f:
            if min_reward is not None:
                q = q.filter(getattr(Task, rew_f) >= min_reward)
            if max_reward is not None:
                q = q.filter(getattr(Task, rew_f) <= max_reward)
        return q.order_by(Task.id.desc()).all()

def get_task(task_id: int):
    with SessionLocal() as s:
        return s.query(Task).filter(Task.id == task_id).first()

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


def _task_field_map() -> dict[str, str | None]:
    """Вернём ВСЕ ключи, даже если столбца нет (значение = None)."""
    title         = "title"        if hasattr(Task, "title")        else ("name" if hasattr(Task, "name") else None)
    description   = "description"  if hasattr(Task, "description")  else None
    reward        = "reward"       if hasattr(Task, "reward")       else ("coins" if hasattr(Task, "coins") else None)
    difficulty    = "difficulty"   if hasattr(Task, "difficulty")   else ("level" if hasattr(Task, "level") else None)
    published     = "published"    if hasattr(Task, "published")    else ("is_published" if hasattr(Task, "is_published") else None)
    deadline_days = "deadline_days"if hasattr(Task, "deadline_days")else ("deadline" if hasattr(Task, "deadline") else None)
    created_at    = "created_at"   if hasattr(Task, "created_at")   else None
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
    t = Task()  # БЕЗ kwargs

    title_f       = fm.get("title")
    desc_f        = fm.get("description")
    reward_f      = fm.get("reward")
    diff_f        = fm.get("difficulty")
    pub_f         = fm.get("published")
    deadline_f    = fm.get("deadline_days")
    created_at_f  = fm.get("created_at")

    if title_f:      setattr(t, title_f, title)
    if desc_f:       setattr(t, desc_f, description)
    if reward_f:     setattr(t, reward_f, reward)
    if diff_f:       setattr(t, diff_f, difficulty)
    if pub_f:        setattr(t, pub_f, False)
    if deadline_f:   setattr(t, deadline_f, deadline_days)
    if created_at_f: setattr(t, created_at_f, datetime.utcnow())

    return t

def list_tasks(*, min_reward: int | None = None, max_reward: int | None = None,
               difficulty: str | None = None, only_published: bool = True) -> list[Task]:
    fm = _task_field_map()
    with SessionLocal() as s:
        q = s.query(Task)
        # опубликовнные
        if only_published and fm["published"]:
            q = q.filter(getattr(Task, fm["published"]) == True)  # noqa: E712
        # сложность
        if difficulty and fm["difficulty"]:
            q = q.filter(getattr(Task, fm["difficulty"]) == difficulty)
        # диапазон награды
        if fm["reward"]:
            if min_reward is not None:
                q = q.filter(getattr(Task, fm["reward"]) >= min_reward)
            if max_reward is not None:
                q = q.filter(getattr(Task, fm["reward"]) <= max_reward)
        return q.order_by(Task.id.desc()).all()

def get_task(task_id: int) -> Task | None:
    with SessionLocal() as s:
        return s.query(Task).filter(Task.id == task_id).first()

def _resolve_user(user_tg_id: int) -> User | None:
    with SessionLocal() as s:
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

# ultil for id
def _get(obj, name, default=None):
    return getattr(obj, name, default)


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


def get_active_assignment(user_tg_id: int, task_id: int) -> Optional[TaskAssignment]:
    
    with SessionLocal() as s:
        a = (
            s.query(TaskAssignment)
            .filter(TaskAssignment.user_tg_id == user_tg_id,
                    TaskAssignment.task_id == task_id,
                    TaskAssignment.status == "active")
            .first()
        )
        return a

# Отметить «взято» (если ещё не взято)
def take_task(user_tg_id: int, task_id: int) -> bool:
    with SessionLocal() as s:
        # уже есть активное?
        exists = (
            s.query(TaskAssignment)
             .filter(TaskAssignment.user_tg_id == user_tg_id,
                     TaskAssignment.status == "active")
             .first()
        )
        if exists:
            return False
        # создать активную
        a = TaskAssignment(user_tg_id=user_tg_id, task_id=task_id, status="active", created_at=datetime.utcnow())
        s.add(a)
        s.commit()
        return True

# Сдача: сохраняем текст/ссылку и (опц.) file_id; статус -> submitted
def submit_task(user_tg_id: int, task_id: int, text: str, file_id: Optional[str] = None) -> bool:
    with SessionLocal() as s:
        a = (
            s.query(TaskAssignment)
            .filter(TaskAssignment.user_tg_id == user_tg_id,
                    TaskAssignment.task_id == task_id,
                    TaskAssignment.status == "active")
            .first()
        )
        if not a:
            return False
        # предполагаем, что в модели есть поля proof_text/proof_file_id; если нет — пропусти
        if hasattr(a, "proof_text"):
            a.proof_text = text
        if file_id and hasattr(a, "proof_file_id"):
            a.proof_file_id = file_id
        a.status = "submitted"
        if hasattr(a, "submitted_at"):
            a.submitted_at = datetime.utcnow()
        s.commit()
        return True
    

# Список «на проверке» для админа
def list_submitted_assignments(limit: int = 20) -> list[TaskAssignment]:
    with SessionLocal() as s:
        return (
            s.query(TaskAssignment)
            .filter(TaskAssignment.status == "submitted")
            .order_by(TaskAssignment.id.desc())
            .limit(limit)
            .all()
        )

# Апрув/реджект модератором; при апруве — начисляем монеты
def moderate_assignment(assignment_id: int, approve: bool) -> Optional[TaskAssignment]:
    with SessionLocal() as s:
        a = s.query(TaskAssignment).filter(TaskAssignment.id == assignment_id).first()
        if not a or a.status != "submitted":
            return None

        a.status = "approved" if approve else "rejected"
        if hasattr(a, "reviewed_at"):
            a.reviewed_at = datetime.utcnow()

        # начислим юзеру монеты при апруве
        if approve:
            u = s.query(User).filter(User.tg_id == a.user_tg_id).first()
            t = s.query(Task).filter(Task.id == a.task_id).first()
            if u and t:
                reward = _get(t, "reward", _get(t, "coins", 0)) or 0
                u.coins = (u.coins or 0) + int(reward)

        s.commit()
        s.refresh(a)
        return a


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
