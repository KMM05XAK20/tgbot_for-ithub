from typing import Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import joinedload
from ..storage.db import SessionLocal
from ..storage.models import Task, TaskAssignment, User
from datetime import datetime, timedelta
import logging


log = logging.getLogger(__name__)


def reward_to_difficulty(reward: int) -> str:
    """
    Маппинг сложности по монетам.
    🟢 easy:   <=5
    🟡 medium: 6..10
    🔴 hard:   >10
    """
    if reward <= 5:
        return "easy"
    elif reward <= 10:
        return "medium"
    else:
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


def admin_create_task(
    *,
    title: str,
    description: str,
    reward: int,
    deadline_days: int,
    difficulty: str | None = None,  # <-- теперь НЕобязательный
) -> int:
    """
    Создание задачи из-под админки.
    Если difficulty не передано — вычисляем автоматически по reward.
    """
    if difficulty is None:
        difficulty = reward_to_difficulty(reward)

    with SessionLocal() as s:
        t = Task(
            title=title,
            description=description,
            reward_coins=reward,  # если у тебя поле называется reward_coins
            difficulty=difficulty,
            deadline_days=deadline_days,
            status="active",
            is_published=True,
        )
        s.add(t)
        s.commit()
        s.refresh(t)
        return t.id


# def admin_create_task(*, title: str, description: str, reward: int, difficulty: str, deadline_days: int) -> int:
#     """difficulty: easy|medium|hard; deadline_days >= 0"""
#     with SessionLocal() as s:
#         difficulty = reward_to_difficulty(reward)
#         t = _create_task_obj(
#             title=title,
#             description=description,
#             reward=reward,
#             difficulty=difficulty,
#             is_published=True,
#             deadline_days=deadline_days,
#         )
#         s.add(t)
#         s.commit()
#         s.refresh(t)
#         return t.id


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
    fm = _task_field_map()
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


# определение сложности задачи
def classify_difficulty(reward: int) -> str:
    if reward <= 5:
        return "easy"
    elif reward <= 10:
        return "medium"
    else:
        return "hard"


def get_active_assignment(user_tg_id: int, task_id: int) -> TaskAssignment | None:
    """
    Возвращает активное/отправленное назначение по заданию для пользователя.
    """
    with SessionLocal() as s:
        stmt = (
            select(TaskAssignment)
            .join(User, TaskAssignment.user_id == User.id)
            .where(
                User.tg_id == user_tg_id,
                TaskAssignment.task_id == task_id,
                TaskAssignment.status.in_(("active", "submitted")),
            )
        )
        return s.execute(stmt).scalar_one_or_none()


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
    reward = (
        "reward"
        if hasattr(Task, "reward")
        else ("coins" if hasattr(Task, "coins") else None)
    )
    difficulty = (
        "difficulty"
        if hasattr(Task, "difficulty")
        else ("level" if hasattr(Task, "level") else None)
    )
    published = (
        "published"
        if hasattr(Task, "published")
        else ("is_published" if hasattr(Task, "is_published") else None)
    )
    deadline_days = (
        "deadline_days"
        if hasattr(Task, "deadline_days")
        else ("deadline" if hasattr(Task, "deadline") else None)
    )
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


def _create_task_obj(
    *, title: str, description: str, reward: int, difficulty: str, deadline_days: int
) -> Task:
    fm = _task_field_map()
    t = Task()  # ВАЖНО: без kwargs!

    if fm["title"]:
        setattr(t, fm["title"], title)
    if fm["description"]:
        setattr(t, fm["description"], description)
    if fm["reward"]:
        setattr(t, fm["reward"], reward)
    if fm["difficulty"]:
        setattr(t, fm["difficulty"], difficulty)
    if fm["published"]:
        setattr(t, fm["published"], False)
    if fm["deadline_days"]:
        setattr(t, fm["deadline_days"], deadline_days)
    if fm["created_at"]:
        setattr(t, fm["created_at"], datetime.utcnow())

    return t


def seed_tasks_if_empty() -> None:
    with SessionLocal() as s:
        count = s.query(Task).count()
        if count > 0:
            return
        samples = [
            dict(
                title="Репост события",
                description="Сделай репост анонса",
                reward=3,
                difficulty="easy",
                deadline_days=2,
            ),
            dict(
                title="Пост в блог",
                description="Напиши короткий пост",
                reward=8,
                difficulty="medium",
                deadline_days=3,
            ),
            dict(
                title="Организуй митап",
                description="Подготовь офлайн-встречу",
                reward=13,
                difficulty="hard",
                deadline_days=7,
            ),
        ]
        for d in samples:
            s.add(_create_task_obj(**d))
        s.commit()


def list_submitted_assignments(limit: int = 20) -> list[TaskAssignment]:
    """Все задания в статусе 'submitted' для админской модерации."""
    with SessionLocal() as s:
        stmt = (
            select(TaskAssignment)
            .where(TaskAssignment.status == "submitted")
            .order_by(TaskAssignment.id.desc())
            .limit(limit)
        )
        res = s.execute(stmt)
        items = [row[0] for row in res.all()]
        # подгружаем связки task/user, чтобы потом можно было их показать
        for ta in items:
            _ = ta.task
            _ = ta.user
        return items


# калькулятор начисления баллов
def calc_reward_for_task(task: Task | None) -> int:
    if task is None:
        return 0
    if getattr(task, "reward_coins", None) is not None:
        return int(task.reward_coins)
    # цена сложностей
    diff_reward_map = {"easy": 3, "medium": 7, "hard": 12}
    return diff_reward_map(getattr(task, "difficulty", ""), 0)


def moderate_assignment(assignment_id: int, approved: bool) -> int:
    """
    Модерация сдачи задания.
    :return: сколько coins начислили (0, если отклонено или ошибка)
    """
    with SessionLocal() as s:
        ta = s.get(TaskAssignment, assignment_id)
        if not ta:
            log.warning("moderate_assignment: assignment %s not found", assignment_id)
            return 0

        # чтобы не начислить второй раз
        if ta.status in ("approved", "done", "rejected"):
            log.warning(
                "moderate_assignment: assignment %s already moderated with status=%s",
                assignment_id,
                ta.status,
            )
            return 0

        user = ta.user
        if not user:
            user = s.get(User, ta.user_id) if ta.user_id else None
        if not user:
            log.error(
                "moderate_assignment: user not found for assignment %s (user_id=%s)",
                assignment_id,
                ta.user_id,
            )
            return 0

        if not approved:
            ta.status = "rejected"
            s.commit()
            log.info(
                "moderate_assignment: REJECT assignment %s for user %s",
                assignment_id,
                user.tg_id,
            )
            return 0

        # считаем награду
        reward = calc_reward_for_task(ta.task)

        before = user.coins or 0
        after = before + reward
        user.coins = after

        ta.status = "approved"
        ta.checked_at = datetime.utcnow() if hasattr(ta, "checked_at") else None

        s.commit()

        log.info(
            "moderate_assignment: APPROVE assignment %s, user %s coins %s -> %s (reward=%s)",
            assignment_id,
            user.tg_id,
            before,
            after,
            reward,
        )
        return reward


def list_tasks(
    *,
    min_reward: int | None = None,
    max_reward: int | None = None,
    difficulty: str | None = None,
    only_published: bool = True,
):
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


def list_public_tasks(difficulty: str | None = None) -> list[Task]:
    """
    Возвращает задачи, которые должны отображаться в каталоге.
    difficulty: "easy" | "medium" | "hard" | "all" | None
    """

    with SessionLocal() as s:
        q = s.query(Task).filter(Task.is_published == True)

        # Если передали фильтр по сложности
        if difficulty and difficulty != "all":
            q = q.filter(Task.difficulty == difficulty)

        q = q.filter(Task.status == "active")
        # Для стабильного порядка
        q = q.order_by(Task.id.asc())

        return q.all()


def debug_all_tasks() -> list[Task]:
    with SessionLocal as s:
        return s.query(Task).order_by(Task.id.asc()).all()


def get_task(task_id: int):
    with SessionLocal() as s:
        return s.query(Task).filter(Task.id == task_id).first()


def has_active_assignment(user_tg_id: int, task_id: int) -> bool:
    """
    Есть ли у пользователя АКТИВНОЕ/ОТПРАВЛЕННОЕ на проверку задание с этим task_id.
    approved/rejected — НЕ считаем активным.
    """

    print(f"[DEBUG has_active_assignment] user_tg_id={user_tg_id}, task_id={task_id}")

    with SessionLocal() as s:
        user = s.query(User).filter(User.tg_id == user_tg_id).first()
        if not user:
            print("[DEBUG has_active_assignment] user not found")
            return False

        q = s.query(TaskAssignment).filter(
            TaskAssignment.user_id == user.id,
            TaskAssignment.task_id == task_id,
            TaskAssignment.status.in_(("active", "submitted")),
        )

        exists = s.query(q.exists()).scalar()
        print("[DEBUG has_active_assignment] exists={exists}")
        return exists

    # with SessionLocal() as s:
    #     user = (
    #         s.query(User)
    #         .filter(User.tg_id == user_tg_id)
    #         .one_or_none()
    #     )
    #     if not user:
    #         return False

    #     existing = (
    #         s.query(TaskAssignment)
    #         .filter(
    #             TaskAssignment.user_id == user.id,
    #             TaskAssignment.task_id == task_id,
    #             TaskAssignment.status.in_(("active", "submitted")),
    #         )
    #         .first()
    #     )
    #     return existing is not None


def take_task(user_tg_id: int, task_id: int) -> bool:
    """
    Пользователь берёт задание.
    Создаём TaskAssignment в статусе active, если ещё не было активного.
    """
    with SessionLocal() as s:
        # ищем / создаём пользователя
        user = s.execute(
            select(User).where(User.tg_id == user_tg_id)
        ).scalar_one_or_none()
        if not user:
            user = User(tg_id=user_tg_id)
            s.add(user)
            s.flush()  # чтобы появился user.id

        task = s.get(Task, task_id)
        if not task:
            log.warning("take_task: task %s not found", task_id)
            return False

        # если есть активное/submitted назначение — не создаём ещё одно
        exists = s.execute(
            select(TaskAssignment).where(
                TaskAssignment.user_id == user.id,
                TaskAssignment.task_id == task_id,
                TaskAssignment.status.in_(("active", "submitted")),
            )
        ).scalar_one_or_none()
        if exists:
            return False

        # выставляем дедлайн в днях
        days = task.deadline_days or 1
        now = datetime.utcnow()
        due_at = now + timedelta(days=days)

        ta = TaskAssignment(
            task_id=task_id,
            user_id=user.id,
            taken_at=now,
            due_at=due_at,
            status="active",
        )
        s.add(ta)
        s.commit()
        return True


def _task_field_map() -> dict[str, str | None]:
    """Вернём ВСЕ ключи, даже если столбца нет (значение = None)."""
    title = (
        "title"
        if hasattr(Task, "title")
        else ("name" if hasattr(Task, "name") else None)
    )
    description = "description" if hasattr(Task, "description") else None
    reward = (
        "reward"
        if hasattr(Task, "reward")
        else ("coins" if hasattr(Task, "coins") else None)
    )
    difficulty = (
        "difficulty"
        if hasattr(Task, "difficulty")
        else ("level" if hasattr(Task, "level") else None)
    )
    published = (
        "published"
        if hasattr(Task, "published")
        else ("is_published" if hasattr(Task, "is_published") else None)
    )
    deadline_days = (
        "deadline_days"
        if hasattr(Task, "deadline_days")
        else ("deadline" if hasattr(Task, "deadline") else None)
    )
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


def _create_task_obj(
    *, title: str, description: str, reward: int, difficulty: str, deadline_days: int
) -> Task:
    fm = _task_field_map()
    t = Task()  # БЕЗ kwargs

    title_f = fm.get("title")
    desc_f = fm.get("description")
    reward_f = fm.get("reward")
    diff_f = fm.get("difficulty")
    pub_f = fm.get("published")
    deadline_f = fm.get("deadline_days")
    created_at_f = fm.get("created_at")

    if title_f:
        setattr(t, title_f, title)
    if desc_f:
        setattr(t, desc_f, description)
    if reward_f:
        setattr(t, reward_f, reward)
    if diff_f:
        setattr(t, diff_f, difficulty)
    if pub_f:
        setattr(t, pub_f, False)
    if deadline_f:
        setattr(t, deadline_f, deadline_days)
    if created_at_f:
        setattr(t, created_at_f, datetime.utcnow())

    return t


def list_tasks(
    *,
    min_reward: int | None = None,
    max_reward: int | None = None,
    difficulty: str | None = None,
    only_published: bool = True,
) -> list[Task]:
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
        return s.execute(
            select(User).where(User.tg_id == user_tg_id)
        ).scalar_one_or_none()


def count_assignments_by_status(user_tg_id: int) -> dict[str, int]:
    """Вернёт агрегаты по группам статусов: active / submitted / done"""
    with SessionLocal() as s:
        user = _resolve_user(s, user_tg_id)
        if not user:
            return {"active": 0, "submitted": 0, "done": 0}
        q = (
            select(TaskAssignment.status, func.count(TaskAssignment.id))
            .where(TaskAssignment.user_id == user.id)
            .group_by(TaskAssignment.status)
        )
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
        a = (
            s.query(TaskAssignment)
            .options(joinedload(TaskAssignment.task), joinedload(TaskAssignment.user))
            .get(assignment_id)
        )
        return a


def count_assignments_by_status(user_tg_id: int) -> dict[str, int]:
    """
    Возвращает количество по группам: active/submitted/done
    active = in_progress; submitted = submitted; done = approved|rejected
    """
    with SessionLocal() as s:
        u = s.execute(select(User).where(User.tg_id == user_tg_id)).scalar_one_or_none()
        if not u:
            return {"active": 0, "submitted": 0, "done": 0}

        base = (
            select(TaskAssignment.status, func.count())
            .where(TaskAssignment.user_id == u.id)
            .group_by(TaskAssignment.status)
        )
        rows = s.execute(base).all()
        raw = {st: cnt for st, cnt in rows}
        active = raw.get("in_progress", 0)
        submitted = raw.get("submitted", 0)
        done = raw.get("approved", 0) + raw.get("rejected", 0)
        return {"active": active, "submitted": submitted, "done": done}


def list_assignments(
    user_tg_id: int, group: str, page: int = 1, per_page: int = 10, diff: str = "all"
):
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
            cond_group = or_(
                TaskAssignment.status == "approved", TaskAssignment.status == "rejected"
            )

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


def moderate_assignment(assignment_id: int, approved: bool) -> bool:
    """
    Модерация заявки:
    - approved=True  → статус 'done', начисляем coins
    - approved=False → статус 'rejected' (без награды)
    """
    with SessionLocal() as s:
        ta: TaskAssignment | None = s.query(TaskAssignment).get(assignment_id)
        if not ta:
            return False

        if ta.status != "submitted":
            # Модерировать есть смысл только "на проверке"
            return False

        task: Task | None = ta.task
        user: User | None = ta.user

        if approved:
            reward = getattr(task, "reward_coins", 0) or 0
            if user:
                user.coins = (user.coins or 0) + reward
            ta.status = "done"
        else:
            ta.status = "rejected"

        s.commit()
        return True


# ultil for id
def _get(obj, name, default=None):
    return getattr(obj, name, default)


def format_dt(dt: datetime | None) -> str:
    if not dt:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M")


def get_assignment_card(assignment_id: int) -> str | None:
    """
    Возвращает готовый текст для карточки назначения задания:
    кто, какое задание, дедлайн, статус, что прислал и т.п.
    """
    with SessionLocal() as s:
        ta: TaskAssignment | None = (
            s.query(TaskAssignment)
            .options(
                joinedload(TaskAssignment.user),
                joinedload(TaskAssignment.task),
            )
            .filter(TaskAssignment.id == assignment_id)
            .one_or_none()
        )

        if not ta:
            return None

        user: User | None = ta.user
        task: Task | None = ta.task

        # --- Пользователь ---
        if user:
            if user.username:
                user_line = f"👤 Пользователь: @{user.username} (tg_id={user.tg_id})"
            else:
                user_line = f"👤 Пользователь: id={user.id}, tg_id={user.tg_id}"
        else:
            user_line = "👤 Пользователь: неизвестен"

        # --- Задание ---
        if task:
            title = task.title or f"task#{task.id}"
            desc = task.description or "без описания"
            reward = getattr(task, "reward_coins", None)
            difficulty = getattr(task, "difficulty", None)

            task_lines = [
                f"📌 Задание: <b>{title}</b>",
                f"ℹ️ Описание: {desc}",
            ]
            if difficulty:
                task_lines.append(f"⭐️ Сложность: {difficulty}")
            if reward is not None:
                task_lines.append(f"💰 Награда: {reward} coins")
            task_block = "\n".join(task_lines)
        else:
            task_block = f"📌 Задание: task_id={ta.task_id}"

        # --- Даты и статус ---
        status = ta.status or "—"
        taken = format_dt(ta.taken_at)
        due = format_dt(ta.due_at)
        submitted = format_dt(ta.submitted_at)

        status_block = (
            f"📊 Статус: <b>{status}</b>\n"
            f"📥 Взято: {taken}\n"
            f"⏰ Дедлайн: {due}\n"
            f"📤 Отправлено на проверку: {submitted}"
        )

        # --- Что прислал пользователь ---
        if ta.submission_text:
            submission_block = f"📝 Ответ:\n{ta.submission_text}"
        elif ta.submission_file_id:
            submission_block = "🖼 Прикреплено фото/файл."
        else:
            submission_block = "🕳 Пользователь ещё ничего не прислал."

        text = (
            "🔎 <b>Заявка на модерацию</b>\n\n"
            f"{user_line}\n\n"
            f"{task_block}\n\n"
            f"{status_block}\n\n"
            f"{submission_block}"
        )

        return text

def get_user(get_assignment_card):
    get = get_assignment_card()
    return get

def list_pending_assignments(limit: int = 20) -> list[dict]:
    """
    Вернуть последние N заданий в статусе 'submitted'
    в виде простых dict'ов (чтобы не ловить DetachedInstanceError).
    """
    with SessionLocal() as s:
        rows = (
            s.query(TaskAssignment, Task, User)
            .join(Task, Task.id == TaskAssignment.task_id)
            .join(User, User.id == TaskAssignment.user_id)
            .filter(TaskAssignment.status == "submitted")
            .order_by(TaskAssignment.id.desc())
            .limit(limit)
            .all()
        )

        items: list[dict] = []
        for assign, task, user in rows:
            items.append(
                {
                    "id": assign.id,
                    "task_id": assign.task_id,
                    "task_title": task.title,
                    "user_id": assign.user_id,
                    "user_tg_id": user.tg_id,
                    "user_username": user.username,
                    "status": assign.status,
                    "taken_at": assign.taken_at,
                    "submitted_at": assign.submitted_at,
                    "submission_text": assign.submission_text,
                    "submission_file_id": assign.submission_file_id,
                    "reward": task.reward_coins or 0,
                }
            )

        log.debug("[pending_assignments] %d items", len(items))
        return items


def get_assignment_for_moderation(assignment_id: int) -> dict | None:
    """
    Достать одно конкретное задание для экрана проверки.
    """
    with SessionLocal() as s:
        row = (
            s.query(TaskAssignment, Task, User)
            .join(Task, Task.id == TaskAssignment.task_id)
            .join(User, User.id == TaskAssignment.user_id)
            .filter(TaskAssignment.id == assignment_id)
            .one_or_none()
        )

        if row is None:
            log.warning(
                "[get_assignment_for_moderation] not found id=%s", assignment_id
            )
            return None

        assign, task, user = row
        return {
            "id": assign.id,
            "task_id": assign.task_id,
            "task_title": task.title,
            "user_id": assign.user_id,
            "user_tg_id": user.tg_id,
            "user_username": user.username,
            "status": assign.status,
            "taken_at": assign.taken_at,
            "submitted_at": assign.submitted_at,
            "submission_text": assign.submission_text,
            "submission_file_id": assign.submission_file_id,
            "reward": task.reward_coins or 0,
        }


def approve_assignment(assignment_id: int) -> bool:
    """
    Одобрить сдачу: поменять статус на 'approved' и начислить монеты.
    """
    with SessionLocal() as s:
        assign: TaskAssignment | None = s.get(TaskAssignment, assignment_id)
        if not assign:
            log.warning("[approve_assignment] assignment %s not found", assignment_id)
            return False

        if assign.status != "submitted":
            log.warning(
                "[approve_assignment] assignment %s has status %s, expected 'submitted'",
                assignment_id,
                assign.status,
            )
            return False

        user: User | None = s.get(User, assign.user_id)
        task: Task | None = s.get(Task, assign.task_id)

        reward = (task.reward_coins or 0) if task else 0

        if user and reward:
            user.coins = (user.coins or 0) + reward
            log.info(
                "[approve_assignment] user %s got +%s coins (now %s)",
                user.tg_id,
                reward,
                user.coins,
            )

        assign.status = "approved"
        s.commit()
        return True


def reject_assignment(assignment_id: int) -> bool:
    """
    Отклонить сдачу: просто поменять статус на 'rejected'.
    """
    with SessionLocal() as s:
        assign: TaskAssignment | None = s.get(TaskAssignment, assignment_id)
        if not assign:
            log.warning("[reject_assignment] assignment %s not found", assignment_id)
            return False

        if assign.status != "submitted":
            log.warning(
                "[reject_assignment] assignment %s has status %s, expected 'submitted'",
                assignment_id,
                assign.status,
            )
            return False

        assign.status = "rejected"
        s.commit()
        return True


def get_assignment_for_admin(assignment_id: int) -> dict | None:
    """
    Одна конкретная заявка по id.
    """
    with SessionLocal() as s:
        row = (
            s.query(
                TaskAssignment,
                Task.title,
                Task.reward_coins,
                Task.difficulty,
                User.username,
                User.tg_id,
            )
            .join(Task, TaskAssignment.task_id == Task.id)
            .join(User, TaskAssignment.user_id == User.id)
            .filter(TaskAssignment.id == assignment_id)
            .one_or_none()
        )

        if row is None:
            return None

        a, title, reward, diff, uname, tg_id = row

        return {
            "id": a.id,
            "task_id": a.task_id,
            "user_id": a.user_id,
            "user_tg_id": tg_id,
            "user_username": uname,
            "task_title": title,
            "task_reward": reward or 0,
            "task_difficulty": diff,
            "status": a.status,
            "submitted_at": a.submitted_at,
            "submission_text": a.submission_text,
            "submission_file_id": a.submission_file_id,
        }


def submit_task(
    user_tg_id: int,
    task_id: int,
    text: str | None,
    file_id: str | None,
) -> bool:
    """
    Сдать задание:
    - Находим юзера по tg_id
    - Берём последнее НЕфинальное назначение по этой задаче
      (status IN ('active', 'submitted', 'taken'))
    - Обновляем текст/файл, submitted_at, статус -> 'submitted'
    """
    if not text and not file_id:
        print("[submit_task] Neither text nor file_id provided")
        return False

    with SessionLocal() as session:
        # 1) юзер по tg_id
        user = session.scalar(select(User).where(User.tg_id == user_tg_id))
        if not user:
            print(f"[submit_task] No user found with tg_id={user_tg_id}")
            return False

        # 2) ищем последнее НЕфинальное назначение
        non_final_statuses = ("active", "submitted", "taken")
        assignment = session.scalar(
            select(TaskAssignment)
            .where(
                TaskAssignment.user_id == user.id,
                TaskAssignment.task_id == task_id,
                TaskAssignment.status.in_(non_final_statuses),
            )
            .order_by(TaskAssignment.id.desc())
        )

        if not assignment:
            print(
                f"[submit_task] No active assignment for user_id={user.id}, task_id={task_id}"
            )
            return False

        if assignment.status in ("approved", "rejected"):
            print(
                f"[submit_task] Latest assignment {assignment.id} alredy final"
                f"({assignment.status}, cannot submit)"
            )
            return False

        # 3) Обновляем сдачу
        assignment.submission_text = text
        assignment.submission_file_id = file_id
        assignment.submitted_at = datetime.utcnow()
        assignment.status = "submitted"

        try:
            session.commit()
            print(
                f"[submit_task] OK: assignment_id={assignment.id} marked as submitted"
            )
            return True
        except Exception as e:
            session.rollback()
            print(f"[submit_task] ERROR on commit: {e}")
            return False


# Список «на проверке» для админа
def list_submitted_assignments(limit: int = 20) -> list[TaskAssignment]:
    """
    Все задания, отправленные на проверку (status='submitted'),
    с заранее подгруженными user и task, чтобы их можно было трогать
    после закрытия Session.
    """
    with SessionLocal() as s:
        q = (
            s.query(TaskAssignment)
            .options(
                joinedload(TaskAssignment.user),
                joinedload(TaskAssignment.task),
            )
            .filter(TaskAssignment.status == "submitted")
            .order_by(TaskAssignment.submitted_at.desc().nullslast())
            .limit(limit)
        )
        items = q.all()

        # на всякий случай «потрогаем» отношения, чтобы точно прогрелись
        for a in items:
            _ = a.user
            _ = a.task

        return items


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
            u = s.query(User).filter(User.tg_id == a.user_id).first()
            t = s.query(Task).filter(Task.id == a.task_id).first()
            if u and t:
                reward = _get(t, "reward", _get(t, "coins", 0)) or 0
                u.coins = (u.coins or 0) + int(reward)

        s.commit()
        s.refresh(a)
        return a
