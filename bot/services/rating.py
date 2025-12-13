from typing import List, Tuple
from sqlalchemy import select, func
from ..storage.db import SessionLocal
from ..storage.models import User


def get_leaderboard(limit: int = 10) -> List[Tuple[int, str | None, int]]:
    """
    Возвращает топ пользователей: [(tg_id, username, coins), ...]
    """
    with SessionLocal() as s:
        stmt = (
            select(
                User.tg_id, User.username, func.coalesce(User.coins, 0).label("coins")
            )
            .order_by(func.coalesce(User.coins, 0).desc(), User.id.asc())
            .limit(limit)
        )
        return [
            (tg_id, username, coins) for tg_id, username, coins in s.execute(stmt).all()
        ]


def get_user_position(user_tg_id: int) -> tuple[int | None, int]:
    """
    Возвращает (позиция, coins). Позиция = 1 + сколько людей имеют coins строго больше.
    Если пользователя нет — (None, 0)
    """
    with SessionLocal() as s:
        u = s.execute(select(User).where(User.tg_id == user_tg_id)).scalar_one_or_none()
        if not u:
            return None, 0
        coins = u.coins or 0
        # сколько пользователей имеют больше монет
        cnt = s.execute(
            select(func.count()).where(func.coalesce(User.coins, 0) > coins)
        ).scalar_one()
        return cnt + 1, coins
