# bot/storage/models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from .db import Base, engine

# --- Users -------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    role = Column(String, nullable=True)          # "active" | "guru" | "helper"
    coins = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

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

    task = relationship("Task")
    user = relationship("User")

# Создаём таблицы ПОСЛЕ объявления всех моделей
Base.metadata.create_all(bind=engine)
