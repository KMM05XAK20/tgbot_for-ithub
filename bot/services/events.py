# bot/services/events.py
from datetime import datetime

from ..storage.db import SessionLocal
from ..storage.models import Event, User


def create_event(
    *,
    title: str,
    description: str | None,
    event_dt: datetime,
    creator_tg_id: int,
) -> Event:
    """
    Создаём событие в календаре.

    :param title: заголовок события
    :param description: описание (может быть None)
    :param event_dt: datetime события
    :param creator_tg_id: Telegram ID пользователя, создавшего событие
    """
    with SessionLocal() as s:
        # Ищем пользователя по tg_id
        user = s.query(User).filter(User.tg_id == creator_tg_id).first()
        user_id = user.id if user else None  # если юзера нет в БД, просто пишем NULL

        ev = Event(
            title=title,
            description=description,
            event_date=event_dt,  # ВАЖНО: имя поля в модели Event
            user_id=user_id,  # а НЕ creator_tg_id
        )
        s.add(ev)
        s.commit()
        s.refresh(ev)
        return ev


def list_events(limit: int = 10) -> list[Event]:
    """Получить ближайшие события (по дате)."""
    with SessionLocal() as s:
        return s.query(Event).order_by(Event.event_date.asc()).limit(limit).all()


def list_upcoming_events(limit: int = 10) -> list[Event]:
    now = datetime.utcnow()

    with SessionLocal() as s:
        return (
            s.query(Event)
            .filter(Event.event_date >= now)
            .order_by(Event.event_date.asc())
            .limit(limit)
            .all()
        )

    # return list_events(limit=limit)
