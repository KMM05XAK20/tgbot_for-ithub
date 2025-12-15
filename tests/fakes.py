from dataclasses import dataclass
from turtle import title
from typing import Optional

from bot.services.tasks import difficulty_condition


@dataclass
class FakeTask:
    id: int = 1
    title: str = "Тестовая задача"
    description: str = "Описание задачи"
    difficulty: str = "easy"
    reward_coins: int = 5
    deadline_days: Optional[int] = None

@dataclass
class FakeAssignment:
    id: int = 1
    task_id: int = 1
    user_id: int = 1
    status: str = "submitted"