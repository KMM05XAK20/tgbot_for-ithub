from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..storage.db import SessionLocal
from ..storage.models import Event

def create_event(user_id: int, title: str, description: str, event_date: datetime):
    with SessionLocal() as session:
        event = Event(user_id=user_id, title=title, description=description, event_date=event_date)
        session.add(event)
        session.commit()

def get_upcoming_events(user_id: int, limit: int = 5):
    with SessionLocal() as session:
        now = datetime.utcnow()
        events = session.query(Event).filter(Event.user_id == user_id, Event.event_date > now).order_by(Event.event_date.asc()).limit(limit).all()
        return events

def get_all_events(user_id: int):
    with SessionLocal() as session:
        events = session.query(Event).filter(Event.user_id == user_id).order_by(Event.event_date.asc()).all()
        return events

def send_event_reminders():
    with SessionLocal() as session:
        now = datetime.utcnow()
        upcoming_events = session.query(Event).filter(Event.event_date > now).all()
        reminders = []
        for event in upcoming_events:
            if event.event_date - now <= timedelta(days=1):  # 1 день до события
                reminders.append(event)
            elif event.event_date - now <= timedelta(hours=1):  # 1 час до события
                reminders.append(event)
        return reminders
