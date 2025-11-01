from typing import Optional
from sqlalchemy.orm import Session
from ..storage.models import User
from ..storage.db import SessionLocal

def get_user(tg_id: int) -> Optional[User]:
    with SessionLocal() as session:
        return session.query(User).filter_by(tg_id=tg_id).first()

def get_or_create_user(tg_id: int, username: str | None = None) -> User:
    with SessionLocal() as session:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if not user:
            user = User(tg_id=tg_id, username=username)
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

def set_role(tg_id: int, role: str) -> None:
    with SessionLocal() as session:
        user = session.query(User).filter_by(tg_id=tg_id).first()
        if user:
            user.role = role
            session.commit()
