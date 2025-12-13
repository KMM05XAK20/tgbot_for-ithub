from ..storage.db import SessionLocal
from ..storage.models import User, Task, TaskAssignment


def collect_admin_stats() -> dict:
    with SessionLocal() as s:
        total_users = s.query(User).count()
        admins_count = s.query(User).filter(User.is_admin == True).count()

        tasks_total = s.query(Task).count()

        try:
            tasks_pub = s.query(Task).filter(Task.is_published == True).count()
        except Exception:
            tasks_pub = 0

        assignments_total = s.query(TaskAssignment).count()
        assignments_active = (
            s.query(TaskAssignment).filter(TaskAssignment.status == "active").count()
        )
        assignments_submitted = (
            s.query(TaskAssignment).filter(TaskAssignment.status == "submitted").count()
        )
        assignments_approved = (
            s.query(TaskAssignment).filter(TaskAssignment.status == "approved").count()
        )
        assignments_rejected = (
            s.query(TaskAssignment).filter(TaskAssignment.status == "rejected").count()
        )

        return {
            "total_users": total_users,
            "admins_count": admins_count,
            "tasks_total": tasks_total,
            "tasks_published": tasks_pub,
            "assignments_total": assignments_total,
            "assignments_active": assignments_active,
            "assignments_submitted": assignments_submitted,
            "assignments_approved": assignments_approved,
            "assignments_rejected": assignments_rejected,
        }


def get_top_users(limit: int = 5) -> list[User]:
    with SessionLocal() as s:
        return s.query(User).order_by(User.coins.desc()).limit(limit).all()
