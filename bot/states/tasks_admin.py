from aiogram.fsm.state import StatesGroup, State


class AdminTaskCreate(StatesGroup):
    title = State()
    description = State()
    reward = State()
    difficulty = State()
    deadline_days = State()
