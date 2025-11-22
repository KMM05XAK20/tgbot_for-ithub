from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ..storage.models import MentorTopic, Task, TaskAssignment
from typing import Sequence

# welcome zone
def welcome_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Начать", callback_data="role:open")
    return kb.as_markup()


# MAIN
def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="menu:open:profile")],
        [InlineKeyboardButton(text="📚 Каталог заданий", callback_data="menu:open:tasks")],
        [InlineKeyboardButton(text="🏆 Рейтинг", callback_data="menu:open:rating")],
        [InlineKeyboardButton(text="🤝 Менторство", callback_data="menu:open:mentorship")],
        [InlineKeyboardButton(text="🗓 Календарь", callback_data="menu:open:calendar")],
        [InlineKeyboardButton(text="⬅️ В начало", callback_data="menu:open:start")],
    ])

# admin
def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧑‍🏫 Менторы", callback_data="admin:mentors")],
        [InlineKeyboardButton(text="📚 Задания", callback_data="admin:tasks")],          # если есть раздел заданий
        [InlineKeyboardButton(text="🕒 На модерации", callback_data="admin:assignments:pending")],
        [InlineKeyboardButton(text="📣 Рассылка", callback_data="admin:broadcast")],     # если есть рассылка
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:open:main")],
    ])


def admin_pending_kb(assignments: Sequence[TaskAssignment]) -> InlineKeyboardMarkup:
    """
    Список заданий на модерации.
    На каждое назначение — отдельная кнопка:
    [@username • Название задания]
    callback_data = 'admin:assign:<assignment_id>'
    """
    rows: list[list[InlineKeyboardButton]] = []

    for a in assignments:
        # Пытаемся аккуратно вытащить пользователя и задание
        user = getattr(a, "user", None)
        task = getattr(a, "task", None)

        if user and getattr(user, "username", None):
            user_part = f"@{user.username}"
        elif user:
            user_part = f"user#{user.id}"
        else:
            user_part = "неизвестный"

        if task and getattr(task, "title", None):
            task_part = task.title
        else:
            task_part = f"task#{a.task_id}"

        text = f"{user_part} • {task_part}"
        # режем, чтобы не упереться в лимиты Телеги
        if len(text) > 64:
            text = text[:61] + "..."

        rows.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"admin:assign:{a.id}",
            )
        ])

    # Кнопка "Назад в админку"
    rows.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="admin:root",   # у тебя уже должен быть такой обработчик
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_grant_kb(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🛡 Выдать админку",
                callback_data=f"admin:grant:{user_id}"
            )
        ]
    ])

def admin_assignment_kb(assignment_id: int) -> InlineKeyboardMarkup:
    """
    Кнопки под конкретным назначением:
    - Одобрить
    - Отклонить
    - Назад к списку
    """
    rows = [
        [
            InlineKeyboardButton(
                text="✅ Одобрить",
                callback_data=f"admin:assign:approve:{assignment_id}",
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"admin:assign:reject:{assignment_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="⬅️ К списку",
                callback_data="admin:assignments:pending",
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=rows)

# admin menu for mentors
def admin_mentors_root_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить ментора", callback_data="admin:mentors:add")],
        [InlineKeyboardButton(text="🗑 Удалить ментора",  callback_data="admin:mentors:remove")],
        [InlineKeyboardButton(text="📋 Список менторов", callback_data="admin:mentors:list")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:panel")],
    ])

# administration tasks
def admin_tasks_root_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить задание", callback_data="admin:tasks:add")],
        [InlineKeyboardButton(text="📋 Список заданий", callback_data="admin:tasks:list")],
        [InlineKeyboardButton(text="🌱 Засеять демо", callback_data="admin:tasks:seed")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:panel")],
    ])

def admin_review_root_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕒 На проверке", callback_data="admin:review:pending")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:panel")],
    ])

def admin_review_item_kb(assignment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"admin:review:{assignment_id}:approve")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin:review:{assignment_id}:reject")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:review:pending")],
    ])

def admin_tasks_list_kb(tasks: list) -> InlineKeyboardMarkup:
    rows = []
    for t in tasks:
        tid = getattr(t, "id", None)
        title = getattr(t, "title", getattr(t, "name", f"task #{tid}"))
        reward = getattr(t, "reward", getattr(t, "coins", None))
        pub = getattr(t, "published", getattr(t, "is_published", False))

        # строка с названием
        label = f"{title}" + (f" • {reward}💰" if reward is not None else "")
        rows.append([InlineKeyboardButton(text=label, callback_data=f"admin:tasks:nop:{tid}")])

        # строка с действиями
        rows.append([
            InlineKeyboardButton(text=("🔓 Опубл." if pub else "🔒 Скрыто"), callback_data=f"admin:tasks:toggle:{tid}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin:tasks:delete:{tid}"),
        ])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin:tasks")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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


def profile_assignment_kb(aid: int, group: str, page: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ К списку", callback_data=f"profile:history:list:{group}:{page}")
    kb.button(text="📜 Разделы", callback_data="profile:history")
    kb.button(text="⬅️ Профиль", callback_data="menu:open:profile")
    kb.adjust(1, 2)
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


def mentor_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Стать ментором", callback_data="mentor:become"))
    kb.add(InlineKeyboardButton(text="Выбрать наставника", callback_data="mentor:choose"))
    kb.adjust(1)
    return kb.as_markup()

def mentor_list_kb(mentors: list) -> InlineKeyboardMarkup:
    rows = []
    for m in mentors:
        title = f"@{m.username}" if m.username else f"ID {m.tg_id}"
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

# roles
def roles_grid_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👤 Активный спикер", callback_data="role:choose:active")
    kb.button(text="📚 Гуру тех.заданий", callback_data="role:choose:guru")
    kb.button(text="🏆 Помогатор", callback_data="role:choose:helper")
    kb.adjust(2)  # по одной в столбик; поменяй на 2/3 для сетки
    return kb.as_markup()
# tasks


def tasks_filters_kb() -> InlineKeyboardMarkup:
    # Создаем клавиатуру с параметром `type`
    kb =InlineKeyboardBuilder()
    kb.add(
        InlineKeyboardButton(text="🟢 Лёгкие", callback_data="tasks:filter:easy"),
        InlineKeyboardButton(text="🟡 Средние", callback_data="tasks:filter:medium"),
        InlineKeyboardButton(text="🔴 Сложные", callback_data="tasks:filter:hard"),
        InlineKeyboardButton(text="📚 Все", callback_data="tasks:filter:all")
    )
    kb.adjust(2, 2)
    return kb.as_markup()



def tasks_list_kb(tasks: list) -> InlineKeyboardMarkup:
    rows = []
    for t in tasks:
        title = getattr(t, "title", getattr(t, "name", "Untitled"))
        reward = getattr(t, "reward", getattr(t, "coins", "—"))
        tid = getattr(t, "id", None)
        rows.append([InlineKeyboardButton(text=f"{title} • {reward}💰", callback_data=f"tasks:view:{tid}")])
    rows.append([InlineKeyboardButton(text="⬅️ Фильтры", callback_data="menu:open:tasks")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def tasks_catalog_kb(tasks: list[Task]) -> InlineKeyboardMarkup:
    """
    Клавиатура для каталога:
    - по кнопке на каждое задание (Подробнее)
    - снизу — фильтры по сложности
    """
    rows: list[list[InlineKeyboardButton]] = []

    # Кнопки "Подробнее" для каждого задания
    for t in tasks:
        # обрежем длинные названия, чтобы клавиатура не разъезжалась
        title_short = t.title if len(t.title) <= 30 else t.title[:27] + "..."
        rows.append([
            InlineKeyboardButton(
                text=f"🔎 {title_short}",
                callback_data=f"tasks:view:{t.id}",
            )
        ])
    
    # Ряд с фильтрами сложности
    rows.append([
        InlineKeyboardButton(text="🟢 Лёгкие", callback_data="tasks:filter:easy"),
        InlineKeyboardButton(text="🟡 Средние", callback_data="tasks:filter:medium"),
    ])
    rows.append([
        InlineKeyboardButton(text="🔴 Сложные", callback_data="tasks:filter:hard"),
        InlineKeyboardButton(text="📚 Все", callback_data="tasks:filter:all"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def task_submit_kb(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Сдать задание", callback_data=f"tasks:submit:{task_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к каталогу", callback_data="menu:open:tasks")],
    ])

def task_details_kb(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Взять задание", callback_data=f"tasks:take:{task_id}")],
        [InlineKeyboardButton(text="📤 Сдать задание", callback_data=f"tasks:submit:{task_id}")],
        [InlineKeyboardButton(text="ℹ️ Подробнее", callback_data=f"tasks:take:{task_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к каталогу", callback_data="menu:open:tasks")],
    ])

# # alias
# def task_view_kb(task_id: int) -> InlineKeyboardMarkup:
#     return task_details_kb(task_id)

def task_view_kb(task_id: int, already_taken: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if already_taken:
        rows.append([InlineKeyboardButton(text="📤 Сдать задание", callback_data=f"tasks:submit:{task_id}")])
    else:
        rows.append([InlineKeyboardButton(text="✅ Взять задание", callback_data=f"tasks:take:{task_id}")])
    
    rows.append([InlineKeyboardButton(text="⬅️ К списку", callback_data="menu:open:tasks")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


# def task_view_kb(task_id: int, already_taken: bool) -> InlineKeyboardMarkup:
#     kb = InlineKeyboardBuilder()
#     if already_taken:
#         kb.button(text="📤 Сдать задание", callback_data=f"tasks:submit:{task_id}")
#     else:
#         kb.button(text="✅ Взять задание", callback_data=f"tasks:take:{task_id}")
#     kb.button(text="ℹ️ Подробнее", callback_data=f"tasks:more:{task_id}")
#     kb.button(text="⬅️ К списку", callback_data="menu:open:tasks")
#     kb.adjust(1)
#     return kb.as_markup()

# rating
def rating_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Обновить", callback_data="menu:open:rating")
    kb.button(text="🏠 Меню", callback_data="menu:open:root")
    kb.adjust(2)
    return kb.as_markup()

# calendar
def calendar_root_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Весь календарь", callback_data="calendar:all")],
        [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:open:main")],
    ])
    return kb

def calendar_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder
    kb.add(InlineKeyboardButton(text="Весь календарь", callback_data="calendar:all"))
    kb.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:open:profile"))
    kb.adjust(2)
    return kb.as_markup()
