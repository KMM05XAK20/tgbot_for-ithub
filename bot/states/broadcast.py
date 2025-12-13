from aiogram.fsm.state import State, StatesGroup


class Broadcast(StatesGroup):
    waiting_message = State()
