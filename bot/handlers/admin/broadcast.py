import asyncio
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram import Bot

from ...states.broadcast import Broadcast
from ...services.users import get_all_user_tg_ids
from ...keyboards.common import admin_tasks_root_kb

logger = logging.getLogger(__name__)

router = Router(name="admin_broadcast")


# 1) Нажали кнопку "📢 Рассылка" в админке
@router.callback_query(F.data == "admin:broadcast")
async def broadcast_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Broadcast.waiting_message)
    await cb.message.edit_text(
        "✉️ <b>Рассылка</b>\n\n"
        "Отправь текст сообщения, который нужно разослать всем пользователям.\n\n"
        "Отмена: /cancel",
        parse_mode=ParseMode.HTML,
    )
    await cb.answer()


# 2) Админ прислал текст рассылки — показываем превью + кнопки
@router.message(Broadcast.waiting_message)
async def broadcast_preview(msg: Message, state: FSMContext):
    text = msg.text
    if not text:
        await msg.answer("Нужен текст для рассылки 🙂 Попробуй ещё раз.")
        return

    await state.update_data(text=text)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="admin:broadcast:send"),
                InlineKeyboardButton(text="✏️ Изменить", callback_data="admin:broadcast:edit"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Отмена", callback_data="admin:broadcast:cancel"),
            ],
        ]
    )

    await msg.answer(
        "Вот так будет выглядеть рассылка:\n\n" + text,
        reply_markup=kb,
        parse_mode=ParseMode.HTML,
    )


# 3) Админ нажал "✏️ Изменить"
@router.callback_query(F.data == "admin:broadcast:edit")
async def broadcast_edit(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Broadcast.waiting_message)
    await cb.message.edit_text(
        "Ок, отправь новый текст рассылки.\n\nОтмена: /cancel",
        parse_mode=ParseMode.HTML,
    )
    await cb.answer()


# 4) Админ нажал "⬅️ Отмена"
@router.callback_query(F.data == "admin:broadcast:cancel")
async def broadcast_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("Рассылка отменена.", reply_markup=admin_tasks_root_kb())
    await cb.answer()


# 5) Админ нажал "✅ Отправить" — реально шлём всем
@router.callback_query(F.data == "admin:broadcast:send")
async def broadcast_send(cb: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    text = data.get("text")

    if not text:
        await cb.answer("Нет текста для рассылки 🤔", show_alert=True)
        return

    user_ids = get_all_user_tg_ids()
    total = len(user_ids)
    sent = 0

    await cb.answer("Запустил рассылку…", show_alert=True)

    for uid in user_ids:
        try:
            await bot.send_message(uid, text, parse_mode=ParseMode.HTML)
            sent += 1
            # маленькая задержка, чтобы не словить flood-limit
            await asyncio.sleep(0.05)
        except Exception as e:
            logger.warning("[broadcast] failed to send to %s: %s", uid, e)

    await state.clear()
    await cb.message.edit_text(
        f"📢 Рассылка завершена.\n\n"
        f"Всего пользователей: {total}\n"
        f"Успешно отправлено: {sent}",
        reply_markup=admin_tasks_root_kb(),
        parse_mode=ParseMode.HTML,
    )
