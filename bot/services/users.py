from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..storage.models import User
from ..storage.db import SessionLocal

def get_user(tg_id: int) -> Optional[User]:
    with SessionLocal() as session:
        return session.query(User).filter_by(tg_id=tg_id).first()

def get_user_by_username(username: str) -> Optional[User]:
    uname = username.lstrip("@").lower()
    with SessionLocal() as s:
        return s.query(User).filter(User.username.ilike(uname)).first()

def get_user_by_tg_id(tg_id: int) -> Optional[User]:
    with SessionLocal() as s:
        return s.query(User).filter(User.tg_id == tg_id).first()

def get_or_create_user(tg_id: int, username: Optional[str] = None) -> User:
    with SessionLocal() as s:
        u = s.query(User).filter(User.tg_id == tg_id).first()
        if u:
            if username and (u.username or "").lower() != username.lstrip("@").lower():
                u.username = username.lstrip("@")
                s.commit()
            return u
        u = User(tg_id=tg_id, username=(username or "").lstrip("@") or None, role=None, coins=0)
        s.add(u)
        s.commit()
        s.refresh(u)
        return u

def set_role(tg_id: int, role: str) -> None:
    with SessionLocal() as session:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if user:
            user.role = role
            session.commit()


def set_admin_status(tg_id: int, is_admin: bool):
    with SessionLocal() as s:
        user = s.query(User).filter(User.tg_id == tg_id).first()
        if user:
            user.is_admin = is_admin
            s.commit()
        return user

def set_user_role(tg_id: int, role: Optional[str]) -> Optional[User]:
    """role: 'guru' | 'helper' | None (снять роль)"""
    assert role in {"guru", "helper", None}
    with SessionLocal() as s:
        u = s.query(User).filter(User.tg_id == tg_id).first()
        if not u:
            return None
        u.role = role
        s.commit()
        s.refresh(u)
        return u
    


def get_recent_users(limit: int = 20) -> list[User]:
    """
    Вернуть последних N пользователей по дате создания.
    """
    with SessionLocal() as s:
        return (
            s.query(User)
            .order_by(desc(User.created_at))
            .limit(limit)
            .all()
        )

def find_user(identifier: str) -> Optional[User]:
    """identifier: '@username' или целое tg_id (строкой)"""
    ident = identifier.strip()
    if ident.startswith("@"):
        return get_user_by_username(ident)
    if ident.isdigit():
        return get_user_by_tg_id(int(ident))
    # fallback: пробуем как username без @
    return get_user_by_username(ident)