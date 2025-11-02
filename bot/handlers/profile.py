from aiogram import Router, F
from aiogram.types import CallbackQuery
from ..services.users import get_user
from ..keyboards.common import profile_kb, main_menu_kb
from ..services.tasks import count_assignments_by_status, list_assignments
from ..services.levels import level_by_coins, render_progress_bar
from ..keyboards.common import profile_history_filters_kb, profile_history_list_kb



router = Router()


def _role_title(code: str | None) -> str:
    mapping = {"active": "Активный спикер", "guru": "Гуру тех.заданий", "helper": "Помогатор"}
    return mapping.get(code or "", "—")

def _group_title(group: str) -> str:
    return {"active": "Активные", "submitted": "На проверке", "done": "Завершённые"}.get(group, "Активные")

def _profile_card(username: str | None, role: str | None, coins: int, position: int | None, badges: list[str], created_at) -> str:
    name_line = f"<b>@{username}</b>" if username else "<b>без никнейма</b>"
    pos_line = f"{position} место" if position is not None else "—"
    badges_line = " • ".join(badges) if badges else "пока нет"
    created = created_at.strftime("%Y-%m-%d") if created_at else "—"

    return (
        "👤 <b>Профиль</b>\n"
        f"{name_line}\n\n"
        f"🎭 Роль: <b>{_role_title(role)}</b>\n"
        f"🪙 Баллы: <b>{coins}</b>\n"
        f"🏆 Рейтинг: <b>{pos_line}</b>\n"
        f"🎖 Бейджи: {badges_line}\n"
        f"📅 С нами с: {created}"
    )


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



@router.callback_query(F.data == "menu:open:profile")
async def open_profile(cb: CallbackQuery):
    user = get_user(cb.from_user.id)
    if not user:
        # На всякий случай — создадим «пустой» профиль
        text = "Профиль не найден. Нажмите /start ещё раз."
        await cb.message.edit_text(text, reply_markup=main_menu_kb())
        return await cb.answer()

    # badges_json в твоей модели может отсутствовать — покажем пусто
    badges: list[str] = []
    # если позже добавишь поле badges_json (строка с JSON), распарси тут

    card = _profile_card(
        username=user.username,
        role=user.role,
        coins=user.coins or 0,
        position=getattr(user, "rating_position", None),
        badges=badges,
        created_at=user.created_at,
    )

    li = level_by_coins(user.coins or 0)

    if li.next_base is None:
        lvl_line = f"🏅 Level: <b>{li.level}</b> (MAX)"
        progress_line = f"{render_progress_bar(li.progress_percent)} 100%"
    else:
        need = li.to_next or 0
        lvl_line = f"🏅 Level: <b>{li.level}</b> · {user.coins}/{li.next_base} coins"
        progress_line = f"{render_progress_bar(li.progress_percent)} {li.progress_percent}%  (to next: {need})"

        await cb.message.edit_text(card, reply_markup=profile_kb())
        await cb.answer()

    position_text = getattr(user, "position", "-")

    text = (
    f"👤 <b>Твой профиль</b>\n"
    f"💰 Coins: <b>{user.coins}</b>\n"
    f"{lvl_line}\n{progress_line}\n"
    f"📊 Рейтинг: {position_text}\n"
    # ...
)

@router.callback_query(F.data == "profile:history")
async def profile_history(cb: CallbackQuery):
    # Заглушка: позже подтянем реальные задания из task_assignments
    text = (
        "📜 <b>История активности</b>\n"
        "Пока пусто. Возвращайся после первых заданий 🙂"
    )
    await cb.message.edit_text(text + "\n\n⬅️ Вернуться в профиль", reply_markup=profile_kb())
    await cb.answer()
