from aiogram.fsm.state import StatesGroup, State

class AdminMentorAdd(StatesGroup):
    waiting_identifier = State()  # ждём @username или telegram_id

class AdminMentorRemove(StatesGroup):
    waiting_identifier = State()
