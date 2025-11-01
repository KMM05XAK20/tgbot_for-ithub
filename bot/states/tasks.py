from aiogram.fsm.state import StatesGroup, State

class TaskSubmit(StatesGroup):
    waiting_proof = State()
