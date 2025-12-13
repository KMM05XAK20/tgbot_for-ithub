from aiogram import Router, F
from aiogram.types import CallbackQuery

from ...filters.roles import IsAdmin
from ...keyboards.common import admin_review_root_kb
from ...services.tasks import moderate_assignment

router = Router(name="admin_review")

# ... остальные хендлеры (review_root, review_pending) без изменений ...


@router.callback_query(IsAdmin(), F.data.regexp(r"^admin:review:\d+:(approve|reject)$"))
async def review_decide(cb: CallbackQuery):
    """
    Ожидаем строго: admin:review:<assignment_id>:(approve|reject)
    Пример: admin:review:42:approve
    """
    try:
        _, _, id_str, action = cb.data.split(":")
        assignment_id = int(id_str)
    except Exception:
        return await cb.answer("Некорректные данные", show_alert=True)

    if action not in {"approve", "reject"}:
        return await cb.answer("Неизвестное действие", show_alert=True)

    updated = moderate_assignment(assignment_id, approve=(action == "approve"))
    if not updated:
        return await cb.answer("Элемент не найден или уже обработан", show_alert=True)

    await cb.message.edit_text(
        f"Готово: статус → {updated.status}", reply_markup=admin_review_root_kb()
    )
    await cb.answer("OK")
