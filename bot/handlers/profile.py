from aiogram import Router, F
from aiogram.types import CallbackQuery
from ..services.users import get_user
from ..keyboards.common import profile_kb, main_menu_kb, profile_history_filters_kb, profile_history_list_kb
from ..services.tasks import count_assignments_by_status, list_assignments
from ..services.levels import level_by_coins, render_progress_bar
from ..services.badges import render_badges_line
from ..services.rating import get_user_position

router = Router()

def _role_title(code: str | None) -> str:
    mapping = {"active": "Активный спикер", "guru": "Гуру тех.заданий", "helper": "Помогатор"}
    return mapping.get(code or "", "—")

def _group_title(group: str) -> str:
    return {"active": "Активные", "submitted": "На проверке", "done": "Завершённые"}.get(group, "Активные")

@router.callback_query(F.data == "menu:open:profile")
async def open_profile(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    if not user:
        await cb.message.edit_text("Профиль не найден. Нажмите /start ещё раз.", reply_markup=main_menu_kb())
        return await cb.answer()

    coins = user.coins or 0
    li = level_by_coins(coins)
    if li.next_base is None:
        lvl_line = f"🏅 Level: <b>{li.level}</b> (MAX)"
        progress_line = f"{render_progress_bar(li.progress_percent)} 100%"
    else:
        need = li.to_next or 0
        lvl_line = f"🏅 Level: <b>{li.level}</b> · {coins}/{li.next_base} coins"
        progress_line = f"{render_progress_bar(li.progress_percent)} {li.progress_percent}%  (to next: {need})"

    badges_line = render_badges_line(coins)

    pos, _ = get_user_position(cb.from_user.id)
    position_text = f"#{pos}" if pos is not None else "—"

    created = user.created_at.strftime("%Y-%m-%d") if getattr(user, "created_at", None) else "—"
    name_line = f"<b>@{user.username}</b>" if user.username else "<b>без никнейма</b>"

    text = (
        "👤 <b>Профиль</b>\n"
        f"{name_line}\n\n"
        f"🎭 Роль: <b>{_role_title(user.role)}</b>\n"
        f"🪙 Баллы: <b>{coins}</b>\n"
        f"{lvl_line}\n{progress_line}\n"
        f"🎖 Бейджи: {badges_line}\n"
        f"🏆 Рейтинг: <b>{position_text}</b>\n"
        f"📅 С нами с: {created}"
    )

    await cb.message.edit_text(text, reply_markup=profile_kb())
    await cb.answer()

@router.callback_query(F.data == "profile:history")
async def profile_history_root(cb: CallbackQuery):
    counts = count_assignments_by_status(cb.from_user.id)
    text = (
        "📜 <b>История активности</b>\n"
        "Выберите категорию:\n"
        "• 🚧 Активные — взятые задания с дедлайном\n"
        "• 🕒 На проверке — отправлены на модерацию\n"
        "• ✅ Завершённые — подтверждены/отклонены"
    )
    await cb.message.edit_text(text, reply_markup=profile_history_filters_kb(counts))
    await cb.answer()
