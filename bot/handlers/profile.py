from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from ..services.users import get_user_by_username
from ..services.tasks import get_user
from ..keyboards.common import profile_kb, main_menu_kb, profile_history_filters_kb, profile_history_list_kb, profile_assignment_kb
from ..services.tasks import count_assignments_by_status, list_assignments, get_assignment_card, reward_to_difficulty
from ..services.levels import level_by_coins, render_progress_bar
from ..services.badges import render_badges_line
from ..services.rating import get_user_position

router = Router(name="profile")

def _group_title(group: str) -> str:
    return {"active": "Активные", "submitted": "На проверке", "done": "Завершённые"}.get(group, "Активные")

def _profile_card(username: str | None, role: str | None, coins: int, position: int | None, badges: list[str], created_at) -> str:
    name_line = f"<b>@{username}</b>" if username else "<b>без никнейма</b>"
    pos_line = f"{position} место" if position is not None else "—"
    badges_line = " • ".join(badges) if badges else "пока нет — всё впереди 🙂"
    created = created_at.strftime("%Y-%m-%d") if created_at else "—"

    return (
        "👤 <b>Твой профиль</b>\n"
        f"{name_line}\n\n"
        f"🎭 Роль: <b>{_role_title(role)}</b>\n"
        f"🪙 Баллы (coins): <b>{coins}</b>\n"
        f"📊 Позиция в рейтинге: <b>{pos_line}</b>\n"
        f"🎖 Бейджи: {badges_line}\n"
        f"📅 В комьюнити с: <b>{created}</b>\n\n"
        "Поднимай уровень, выполняя задания. Чем выше уровень — тем больше доверия и возможностей 🚀"
    )


@router.message(Command("profile"))
async def open_profile(msg: Message):
    user_id = msg.from_user.id
    
    # Получаем профиль пользователя
    profile_data = get_user_by_username(user_id)  # Извлекаем данные из базы данных
    badges = get_user(user_id)  # Получаем бейджи пользователя

    # Формируем текст профиля
    profile_text = _profile_card(
        username=profile_data.username,
        role=profile_data.role,
        coins=profile_data.coins,
        position=profile_data.position,
        badges=badges,
        created_at=profile_data.created_at,
    )

    # Отправляем сообщение с профилем
    await msg.answer(profile_text, reply_markup=profile_kb())


def _role_title(role: str) -> str:
    roles = {
        "admin": "Админ",
        "mentor": "Наставник",
        "user":"Пользователь",
    }
    return roles.get(role, "Неизвестная роль")

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

# список по группе с пагинацией
@router.callback_query(F.data.startswith("profile:history:list:"))
async def profile_history_list(cb: CallbackQuery):
    parts = cb.data.split(":")
    group = parts[3]
    page = max(1, int(parts[4]))
    diff = parts[5] if len(parts) > 5 else "all"

    rows = list_assignments(cb.from_user.id, group=group, page=page, per_page=10, diff=diff)

    group_title = {"active": "Активные", "submitted": "На проверке", "done": "Завершённые"}.get(group, "Активные")

    if not rows:
        text = f"📜 <b>{group_title}</b> · сложность: {diff}\nПока пусто."
        kb = profile_history_list_kb(group, page, diff)
        await _safe_edit(cb.message, text, kb)
        return await cb.answer("Обновлено")

    def diff_icon(reward: int | None) -> str:
        m = reward_to_difficulty(reward)
        return {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(m, "•")

    lines = [f"📜 <b>{group_title}</b> · сложность: {diff} (стр. {page})", ""]
    for aid, title, status, reward, due_at, submitted_at in rows:
        when = due_at.strftime("%Y-%m-%d %H:%M") if due_at else (submitted_at.strftime("%Y-%m-%d %H:%M") if submitted_at else "—")
        mark = {"in_progress": "🚧", "submitted": "🕒", "approved": "✅", "rejected": "❌"}.get(status, "•")
        dmark = diff_icon(reward)
        lines.append(f"{mark} {dmark} <b>{title}</b> — {reward}c — {when} — id:{aid}")
    lines.append("")
    lines.append("Открой карточку: отправь <code>my:assign:view:&lt;id&gt;</code>")

    text = "\n".join(lines)
    kb = profile_history_list_kb(group, page, diff)
    await _safe_edit(cb.message, text, kb)
    await cb.answer("Обновлено")


async def _safe_edit(message, text: str, reply_markup=None):
    """Редактировать без 'message is not modified' ошибок."""
    # 1) если текст идентичен — пробуем обновить только клавиатуру
    if (message.text or "") == text:
        try:
            await message.edit_reply_markup(reply_markup=reply_markup)
            return
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
            return
    # 2) иначе обновляем и текст, и клавиатуру
    try:
        await message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            # На всякий случай ещё раз попробуем обновить только клавиатуру
            try:
                await message.edit_reply_markup(reply_markup=reply_markup)
            except TelegramBadRequest:
                pass
        else:
            raise


# карточка по текстовой команде
@router.callback_query(F.data.startswith("my:assign:view:"))
async def profile_assign_view_cb(cb: CallbackQuery):
    # на случай, если сделаешь кнопку — оставлен роутер для cb
    aid = int(cb.data.split(":")[-1])
    await _send_assignment_card(cb, aid, group="active", page=1)  # дефолты

@router.message(F.text.startswith("my:assign:view:"))
async def profile_assign_view_cmd(msg):
    try:
        aid = int(msg.text.split(":")[-1])
    except Exception:
        return await msg.answer("Формат: my:assign:view:<id>")
    # без контекста группы/страницы покажем базово
    await _send_assignment_card(msg, aid, group="active", page=1)

async def _send_assignment_card(target, assignment_id: int, group: str, page: int):
    a = get_assignment_card(assignment_id)
    if not a:
        if hasattr(target, "answer"):
            return await target.answer("Заявка не найдена.")
        return
    

    when = a["due_at"].strftime("%Y-%m-%d %H:%M") if a["due_at"] else (a["submitted_at"].strftime("%Y-%m-%d %H:%M") if a["submitted_at"] else "—")
    mark = {"in_progress": "🚧", "submitted": "🕒", "approved": "✅", "rejected": "❌"}.get(a["status"], "•")
    dmark = {"easy":"🟢","medium":"🟡","hard":"🔴"}[reward_to_difficulty(a["reward"])]
    sub = a["submission_text"] or "(нет текста)"
    file_note = "да" if a["has_file"] else "нет"

    text = (
        f"📄 <b>Заявка #{a['id']}</b>\n"
        f"{mark} {dmark} <b>{a['task_title']}</b> — {a['reward']}c\n"
        f"{mark} <b>{a['task_title']}</b> — {a['reward']}c\n"
        f"⏱ Срок/дата: {when}\n"
        f"📥 Текст: {sub}\n"
        f"🖼️ Файл: {file_note}\n"
        f"Статус: <b>{a['status']}</b>"
    )

    # target может быть Message или CallbackQuery.message — используем .answer()
    await target.answer(text, reply_markup=profile_assignment_kb(a['id'], group, page), disable_web_page_preview=True)