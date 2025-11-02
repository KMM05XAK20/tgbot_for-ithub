from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# admin
def admin_root_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🕒 На проверке", callback_data="admin:pending:1")
    kb.button(text="🏠 Меню", callback_data="menu:open:root")
    kb.adjust(1)
    return kb.as_markup()

def admin_pending_kb(page: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    prev_cb = f"admin:pending:{max(1, page-1)}"
    next_cb = f"admin:pending:{page+1}"
    kb.button(text="⬅️", callback_data=prev_cb)
    kb.button(text="➡️", callback_data=next_cb)
    kb.button(text="🏠 Меню", callback_data="menu:open:root")
    kb.adjust(3)
    return kb.as_markup()

def admin_assignment_kb(aid: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Approve", callback_data=f"admin:approve:{aid}")
    kb.button(text="❌ Reject", callback_data=f"admin:reject:{aid}")
    kb.button(text="⬅️ Список", callback_data="admin:pending:1")
    kb.adjust(2, 1)
    return kb.as_markup()

# people
def profile_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📜 История активности", callback_data="profile:history")
    kb.button(text="⬅️ Назад в меню", callback_data="menu:open:root")
    kb.adjust(1)
    return kb.as_markup()

def profile_history_filters_kb(counts: dict[str, int]) -> InlineKeyboardMarkup:
    a = counts.get("active", 0)
    s = counts.get("submitted", 0)
    d = counts.get("done", 0)
    kb = InlineKeyboardBuilder()
    kb.button(text=f"🚧 Активные ({a})", callback_data="profile:history:list:active:1")
    kb.button(text=f"🕒 На проверке ({s})", callback_data="profile:history:list:submitted:1")
    kb.button(text=f"✅ Завершённые ({d})", callback_data="profile:history:list:done:1")
    kb.button(text="⬅️ Профиль", callback_data="menu:open:profile")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()


def profile_history_list_kb(group: str, page: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️", callback_data=f"profile:history:list:{group}:{max(1, page-1)}")
    kb.button(text="➡️", callback_data=f"profile:history:list:{group}:{page+1}")
    kb.button(text="📜 Разделы", callback_data="profile:history")
    kb.button(text="⬅️ Профиль", callback_data="menu:open:profile")
    kb.adjust(2, 2)
    return kb.as_markup()

def profile_assignment_kb(aid: int, group: str, page: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ К списку", callback_data=f"profile:history:list:{group}:{page}")
    kb.button(text="📜 Разделы", callback_data="profile:history")
    kb.button(text="⬅️ Профиль", callback_data="menu:open:profile")
    kb.adjust(1, 2)
    return kb.as_markup()

def welcome_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Начать", callback_data="role:open")
    return kb.as_markup()

def roles_grid_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👤 Активный спикер", callback_data="role:choose:active")
    kb.button(text="📚 Гуру тех.заданий", callback_data="role:choose:guru")
    kb.button(text="🏆 Помогатор", callback_data="role:choose:helper")
    kb.adjust(1)  # по одной в столбик; поменяй на 2/3 для сетки
    return kb.as_markup()

def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👤 Мой профиль", callback_data="menu:open:profile")
    kb.button(text="📚 Каталог заданий", callback_data="menu:open:tasks")
    kb.button(text="🏆 Рейтинг", callback_data="menu:open:rating")
    kb.button(text="🤝 Менторство", callback_data="menu:open:mentorship")
    kb.button(text="🗓️ Календарь", callback_data="menu:open:calendar")
    kb.button(text="🎯 Прокачка", callback_data="menu:open:courses")
    kb.button(text="⚙️ Помощь", callback_data="menu:open:help")
    kb.adjust(2)  # сетка 2xN
    return kb.as_markup()

def tasks_filters_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🟢 Легкие", callback_data="tasks:filter:easy:1")
    kb.button(text="🟡 Средние", callback_data="tasks:filter:medium:1")
    kb.button(text="🔴 Сложные", callback_data="tasks:filter:hard:1")
    kb.button(text="🗂 Все", callback_data="tasks:filter:all:1")
    kb.adjust(2, 2)
    return kb.as_markup()

def tasks_list_kb(difficulty: str, page: int, tasks: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    """tasks: [(id, title), ...]"""
    kb = InlineKeyboardBuilder()
    for tid, title in tasks:
        kb.button(text=f"📌 {title}", callback_data=f"tasks:view:{tid}")
    # пагинация
    prev_cb = f"tasks:filter:{difficulty}:{max(1, page-1)}"
    next_cb = f"tasks:filter:{difficulty}:{page+1}"
    kb.button(text="⬅️", callback_data=prev_cb)
    kb.button(text="➡️", callback_data=next_cb)
    kb.button(text="🏠 Меню", callback_data="menu:open:root")
    kb.adjust(1, 3, 1)
    return kb.as_markup()


def task_view_kb(task_id: int, already_taken: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if already_taken:
        kb.button(text="📤 Сдать задание", callback_data=f"tasks:submit:{task_id}")
    else:
        kb.button(text="✅ Взять задание", callback_data=f"tasks:take:{task_id}")
    kb.button(text="ℹ️ Подробнее", callback_data=f"tasks:more:{task_id}")
    kb.button(text="⬅️ К списку", callback_data="menu:open:tasks")
    kb.adjust(1)
    return kb.as_markup()


def rating_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Обновить", callback_data="menu:open:rating")
    kb.button(text="🏠 Меню", callback_data="menu:open:root")
    kb.adjust(2)
    return kb.as_markup()
