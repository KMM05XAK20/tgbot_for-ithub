from aiogram import Router, F
from aiogram.types import CallbackQuery

from ...services.admin_stats import collect_admin_stats, get_top_users
from ...keyboards.common import admin_panel_kb

router = Router(name="admin_stats")

@router.callback_query(F.data == "admin:stats")
async def admin_stats_handler(cb: CallbackQuery):
    data = collect_admin_stats()
    top_users = get_top_users(5)

    lines = []


    lines.append("👥 <b>Пользователи</b>")
    lines.append(f"• Всего: <b>{data['total_users']}</b>")
    lines.append(f"• Администраторов: <b>{data['admins_count']}</b>\n")

    lines.append("📋 <b>Задания</b>")
    lines.append(f"• Всего задач: <b>{data['tasks_total']}</b>")
    lines.append(f"• Опубликовано: <b>{data['tasks_published']}</b>\n")

    lines.append("✅ <b>Назначения</b>")
    lines.append(f"• Всего выдач: <b>{data['assignments_total']}</b>")
    lines.append(f"• Активные: <b>{data['assignments_active']}</b>")
    lines.append(f"• На модерации: <b>{data['assignments_submitted']}</b>")
    lines.append(f"• Одобрено: <b>{data['assignments_approved']}</b>")
    lines.append(f"• Отклонено: <b>{data['assignments_rejected']}</b>\n")


    if top_users:
        lines.append("🏆 <b>Топ по coins</b>")
        for idx, u in enumerate(top_users, start=1):
            name = f"@{u.username}" if u.username else f"id={u.tg_id}"
            coins = u.coins or 0
            lines.append(f"{idx}. {name} - <b>{coins}</b>🪙")

    
    text = "📊 <b>Статистика бота</b>\n\n" + "\n".join(lines)

    await cb.message.edit_text(text, reply_markup=admin_panel_kb())
    await cb.answer()