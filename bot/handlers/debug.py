from aiogram import Router
from aiogram.types import CallbackQuery, Message

router = Router(name="debug")

@router.callback_query()
async def _debug_cb(cb: CallbackQuery):
    print(f"[DEBUG] CB data={cb.data}")
    await cb.answer()

@router.message()
async def _debug_msg(msg: Message):
    print(f"[DEBUG] MSG text={msg.text}")