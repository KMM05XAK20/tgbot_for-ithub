from aiogram.fsm.state import StatesGroup, State


class TaskSubmit(StatesGroup):
    # один шаг: ждём текст/ссылку ИЛИ файл
    waiting_proof = State()
