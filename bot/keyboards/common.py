from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def profile_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📜 История активности", callback_data="profile:history")
    kb.button(text="⬅️ Назад в меню", callback_data="menu:open:root")
    kb.adjust(1)
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
