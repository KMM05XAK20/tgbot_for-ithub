from typing import Optional
from sqlalchemy.orm import Session
from ..storage.db import SessionLocal
from ..storage.models import MentorApplication, MentorTopic, User
from datetime import datetime

MENTOR_RULES = {"guru", "helper"}

def create_mentor_application(user_id: int, mentor_id: int, topic: str):
    """
    Создает заявку на менторство для пользователя.
    """
    with SessionLocal() as s:
        application = MentorApplication(
            user_id=user_id,
            mentor_id=mentor_id,
            topic=topic,
            created_at=datetime.utcnow(),
            status="pending"
        )
        s.add(application)
        s.commit()

def get_mentor_list() -> list[User]:
    with SessionLocal() as s:
        return(
            s.query(User)
            .filter(User.role.in_(list(MENTOR_RULES)))
            .order_by(User.coins.desc().nullslast()
            )
            .all()
        )




def create_mentor_application(user_id: int, mentor_id: int, topic: MentorTopic) -> MentorApplication:
    with SessionLocal() as s:
        exists = (
            s.query(MentorApplication)
            .filter(
                MentorApplication.user_id == user_id,
                MentorApplication.mentor_id == mentor_id,
                MentorApplication.topic == topic.value,
                MentorApplication.status == "pending",
            )
            .all()
        )
        if exists:
            return exists
        app = MentorApplication(
            user_id=user_id,
            mentor_id=mentor_id,
            topic=topic.value,
            status="pending",
        )
        s.add(app)
        s.commit()
        s.refresh(app)
        return app
    

# read
def get_user_applications(user_id: int):
    with SessionLocal() as s:
        return (
            s.query(MentorApplication)
            .filter(MentorApplication.user_id == user_id)
            .order_by(MentorApplication.created_at.desc())
            .all()
        )


# record
def create_mentor_application(user_id: int, mentor_id: int, topic: MentorTopic):
    with SessionLocal() as s:
        exists = (
            s.query(MentorApplication)
            .filter(
                MentorApplication.user_id == user_id,
                MentorApplication.mentor_id == mentor_id,
                MentorApplication.topic == topic.value,
                MentorApplication.status == "pending",
            )
            .first()
        )
        if exists:
            return exists
        app = MentorApplication(
            user_id=user_id,
            mentor_id=mentor_id,
            topic=topic.value,
            status="pending",
        )
        s.add(app)
        s.commit()
        s.refresh(app)
        return app


def get_incoming_for_mentor(mentor_id: int, status: str = "pending") -> list[MentorApplication]:
    with SessionLocal() as s:
        q = s.query(MentorApplication).filter(MentorApplication.mentor_id == mentor_id)
        if status:
            q = q.filter(MentorApplication.status == status)
        return q.order_by(MentorApplication.created_at.desc()).all()


def set_application_status(app_id: int, mentor_id: int, status: str, comment: Optional[str] = None) -> Optional[MentorApplication]:
    """Ментор апдейтит статус своей заявки."""
    assert status in {"approved", "rejected"}
    with SessionLocal() as s:
        app = (
            s.query(MentorApplication)
            .filter(MentorApplication.id == app_id, MentorApplication.mentor_id == mentor_id)
            .first()
        )
        if not app or app.status != "pending":
            return None
        app.status = status
        app.decided_at = datetime.utcnow()
        if comment:
            app.comment = comment
        s.commit()
        s.refresh(app)
        return app

# def get_mentor_applications(mentor_id: int):
#     with SessionLocal() as session:
#         return session.query(MentorApplication).filter(MentorApplication.mentor_id == mentor_id).all()
