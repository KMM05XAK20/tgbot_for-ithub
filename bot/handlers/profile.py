from aiogram import Router, F
from aiogram.types import CallbackQuery
from ..services.users import get_user
from ..keyboards.common import profile_kb, main_menu_kb, profile_history_filters_kb, profile_history_list_kb, profile_assignment_kb
from ..services.tasks import count_assignments_by_status, list_assignments, get_assignment_card, reward_to_difficulty
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

# список по группе с пагинацией
@router.callback_query(F.data.startswith("profile:history:list:"))
async def profile_history_list(cb: CallbackQuery):
    parts = cb.data.split(":")
    # варианты:
    # profile:history:list:<group>:<page>
    # profile:history:list:<group>:<page>:<diff>
    group = parts[3]
    page = max(1, int(parts[4]))
    diff = parts[5] if len(parts) > 5 else "all"

    rows = list_assignments(cb.from_user.id, group=group, page=page, per_page=10, diff=diff)

    group_title = {"active": "Активные", "submitted": "На проверке", "done": "Завершённые"}.get(group, "Активные")
    if not rows:
        text = f"📜 <b>{group_title}</b> · сложность: {diff}\nПока пусто."
        await cb.message.edit_text(text, reply_markup=profile_history_list_kb(group, page, diff))
        return await cb.answer()

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

    await cb.message.edit_text("\n".join(lines), reply_markup=profile_history_list_kb(group, page, diff), disable_web_page_preview=True)
    await cb.answer()


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