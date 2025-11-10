# bot/storage/models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from .db import Base, engine
import enum

# --- Users -------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    role = Column(String, nullable=True)          # "active" | "guru" | "helper"
    coins = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

#--- Mentors ------------------------------------------------------------------

class MentorTopic(enum.Enum):
    CAREER = "Career"
    CONTENT = "Content"
    PROJECTS = "Projects"
    IDEAS = "Ideas"

class MentorApplication(Base):
    __tablename__ = 'mentor_applications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    mentor_id = Column(Integer, ForeignKey('users.id'))
    topic = Column(Enum(MentorTopic))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum("pending", "accepted", "rejected", name="application_status"), default="pending")
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    decided_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    mentor = relationship("User", foreign_keys=[mentor_id])

# --- Tasks -------------------------------------------------------------------
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String, nullable=False)   # "easy" | "medium" | "hard"
    reward_coins = Column(Integer, default=1)
    deadline_hours = Column(Integer, default=48)
    status = Column(String, default="active")     # "active" | "archived"

# --- Task assignments ---------------------------------------------------------
class TaskAssignment(Base):
    __tablename__ = "task_assignments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    taken_at = Column(DateTime, default=datetime.utcnow)
    due_at = Column(DateTime, nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    status = Column(String, default="in_progress")  # "in_progress" | "submitted" | "approved" | "rejected"

    submission_text = Column(Text, nullable=True)      # ссылка/описание
    submission_file_id = Column(String, nullable=True) # file_id фото/видео/док

    task = relationship("Task")
    user = relationship("User")

# -- Calendar -------------------------------------------------------------------
class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    event_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship("User", back_populates="events")

User.events = relationship("Event", back_populates="user", lazy='dynamic')


# Создаём таблицы ПОСЛЕ объявления всех моделей
Base.metadata.create_all(bind=engine)
