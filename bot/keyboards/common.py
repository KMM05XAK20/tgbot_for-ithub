from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ..storage.models import MentorTopic
# admin

def admin_panel_kb() -> InlineKeyboardMarkup:
    """Главное меню админки."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧑‍🏫 Менторы", callback_data="admin:mentors")],
        [InlineKeyboardButton(text="📚 Задания", callback_data="admin:tasks")],          # если есть раздел заданий
        [InlineKeyboardButton(text="📣 Рассылка", callback_data="admin:broadcast")],     # если есть рассылка
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:open:main")],
    ])
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


def admin_mentors_root_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить ментора", callback_data="admin:mentors:add")],
        [InlineKeyboardButton(text="🗑 Удалить ментора",  callback_data="admin:mentors:remove")],
        [InlineKeyboardButton(text="📋 Список менторов", callback_data="admin:mentors:list")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:panel")],
    ])

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

def profile_history_list_kb(group: str, page: int, diff: str = "all") -> InlineKeyboardMarkup:
    diff = (diff or "all").lower()
    def chip(label: str, key: str):
        # подсветим выбранный
        mark = "•" if key == diff else ""
        return f"{label}{' ' + mark if mark else ''}"

    kb = InlineKeyboardBuilder()
    # строка фильтров сложности
    kb.button(text=chip("Все", "all"),    callback_data=f"profile:history:list:{group}:{page}:all")
    kb.button(text=chip("🟢", "easy"),    callback_data=f"profile:history:list:{group}:{page}:easy")
    kb.button(text=chip("🟡", "medium"),  callback_data=f"profile:history:list:{group}:{page}:medium")
    kb.button(text=chip("🔴", "hard"),    callback_data=f"profile:history:list:{group}:{page}:hard")
    kb.adjust(4)

    # навигация
    kb.button(text="⬅️", callback_data=f"profile:history:list:{group}:{max(1, page-1)}:{diff}")
    kb.button(text="➡️", callback_data=f"profile:history:list:{group}:{page+1}:{diff}")
    kb.button(text="📜 Разделы", callback_data="profile:history")
    kb.button(text="⬅️ Профиль", callback_data="menu:open:profile")
    kb.adjust(2, 2)
    return kb.as_markup()


# mentors
def mentorship_root_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Выбрать наставника", callback_data="mentor:choose")],
        [InlineKeyboardButton(text="🗂 Мои заявки", callback_data="mentor:myapps")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:open:main")],
    ])
    return kb


def mentor_role_kb(tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Гуру",    callback_data=f"admin:mentors:setrole:{tg_id}:guru")],
        [InlineKeyboardButton(text="🧰 Помогатор", callback_data=f"admin:mentors:setrole:{tg_id}:helper")],
        [InlineKeyboardButton(text="Отмена", callback_data="admin:mentors")],
    ])


def mentor_menu_kb():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(text="Стать ментором", callback_data="mentor:become"))
    kb.add(InlineKeyboardButton(text="Выбрать наставника", callback_data="mentor:choose"))
    return kb

def mentor_list_kb(mentors: list) -> InlineKeyboardMarkup:
    rows = []
    for m in mentors:
        title = f"@{m.username}" if m.username else f"ID {m.telegram_id}"
        rows.append([InlineKeyboardButton(text=title, callback_data=f"mentor:pick:{m.id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:open:mentorship")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mentor_topics_kb(mentor_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🎯 Карьера", callback_data=f"mentor:topic:{mentor_id}:{MentorTopic.CAREER.value}")],
        [InlineKeyboardButton(text="📱 Контент", callback_data=f"mentor:topic:{mentor_id}:{MentorTopic.CONTENT.value}")],
        [InlineKeyboardButton(text="🔧 Проекты", callback_data=f"mentor:topic:{mentor_id}:{MentorTopic.PROJECTS.value}")],
        [InlineKeyboardButton(text="💡 Идеи",   callback_data=f"mentor:topic:{mentor_id}:{MentorTopic.IDEAS.value}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="mentor:choose")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mentor_confirm_kb(mentor_id: int, topic: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить заявку", callback_data=f"mentor:confirm:{mentor_id}:{topic}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"mentor:topic_back:{mentor_id}")],
    ])

def mentor_inbox_kb(app_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"mentor:app:{app_id}:approve")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mentor:app:{app_id}:reject")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="mentor:inbox")],
    ])


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


def calendar_root_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Весь календарь", callback_data="calendar:all")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:open:main")],
    ])
    return kb


def calendar_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton(text="Весь календарь", callback_data="calendar:all"))
    kb.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:open:profile"))
    return kb
