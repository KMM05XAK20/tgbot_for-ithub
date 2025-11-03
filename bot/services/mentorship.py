from sqlalchemy.orm import Session
from ..storage.db import SessionLocal
from ..storage.models import MentorApplication, User
from datetime import datetime

def create_mentor_application(user_id: int, mentor_id: int, topic: str):
    """
    Создает заявку на менторство для пользователя.
    """
    with SessionLocal() as session:
        application = MentorApplication(
            user_id=user_id,
            mentor_id=mentor_id,
            topic=topic,
            created_at=datetime.utcnow(),
            status="pending"
        )
        session.add(application)
        session.commit()

def create_mentor_application(user_id: int, mentor_id: int, topic: str):
    with SessionLocal() as session:
        application = MentorApplication(user_id=user_id, mentor_id=mentor_id, topic=topic)
        session.add(application)
        session.commit()

def get_mentor_list():
    with SessionLocal() as session:
        return session.query(User).filter(User.role == "guru").all()

def get_mentor_applications(mentor_id: int):
    with SessionLocal() as session:
        return session.query(MentorApplication).filter(MentorApplication.mentor_id == mentor_id).all()
