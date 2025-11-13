from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from ..keyboards.common import rating_kb
from ..services.rating import get_leaderboard, get_user_position

router = Router(name="rating")

@router.message(Command("rating"))
async def rating_cmd(msg: Message):
    await send_rating(msg)

@router.callback_query(F.data == "menu:open:rating")
async def rating_open(cb: CallbackQuery):
    await send_rating(cb.message)
    await cb.answer()

async def send_rating(target: Message):
    top = get_leaderboard(10)
    you_pos, you_coins = get_user_position(target.from_user.id)

    lines = ["🏆 <b>Топ-10</b>"]
    if not top:
        lines.append("Пока пусто.")
    else:
        for i, (tg_id, username, coins) in enumerate(top, start=1):
            user = f"@{username}" if username else f"id:{tg_id}"
            crown = " 👑" if i == 1 else ""
            lines.append(f"{i}. {user} — <b>{coins}</b> coins{crown}")

    you_line = "—"
    if you_pos is not None:
        you_line = f"Ваше место: <b>#{you_pos}</b> · <b>{you_coins}</b> coins"

    text = "\n".join(lines) + f"\n\n{you_line}"
    await target.answer(text, reply_markup=rating_kb())
