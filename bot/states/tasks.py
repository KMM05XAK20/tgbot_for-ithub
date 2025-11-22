from aiogram.fsm.state import StatesGroup, State

class TaskSubmit(StatesGroup):
    waiting_proof = State()

class TaskCreateStates(StatesGroup):
    waiting_title = State()        # ждём название
    waiting_description = State()  # ждём описание
    waiting_reward = State()       # ждём награду (coins)
    waiting_deadline = State()     # ждём дедлайн (часы/дни)