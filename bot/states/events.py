from aiogram.fsm.state import StatesGroup, State

class AdminEventForm(StatesGroup):
    waiting_title       = State()
    waiting_description = State()
    waiting_date        = State()
    waiting_time        = State()