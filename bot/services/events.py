from datetime import datetime
from typing import List

from ..storage.db import SessionLocal
from ..storage.models import Event, User

def create_event(*, title: str, description: str | None, event_dt: datetime,  creator_user_id: int | None = None) -> int:

    with SessionLocal() as s:
        user_id = None
        if creator_user_id is not None:
            user = s.query(User).filter_by(tg_id=creator_user_id).first()
            if user:
                user_id = user_id

        ev = Event(
            title=title,
            description=description,
            event_dt=event_dt,
            user_id=user_id,
        )
        s.add(ev)
        s.commit()
        s.refresh(ev)
        return ev.id

def list_upcoming_events(limit: int = 10) -> List[Event]:

    now = datetime.utcnow()

    with SessionLocal() as s:
        rows = (
            s.query(Event)
            .filter(Event.created_at >= now)
            .order_by(Event.created_at.asc())
            .limit(limit)
            .all()
        )
        return rows