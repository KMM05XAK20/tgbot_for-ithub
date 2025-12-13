# bot/services/badges.py
from dataclasses import dataclass
from .levels import level_by_coins

# Какие уровни дают бейджи:
# можно менять пороги/названия — хранить централизованно тут
BADGE_BY_LEVEL: dict[int, tuple[str, str]] = {
    1: ("Новичок", "🟢"),
    3: ("Активист", "🔸"),
    5: ("Про", "🟣"),
    7: ("Ментор", "🛠️"),
    9: ("Легенда", "🏆"),
}


@dataclass
class Badge:
    level: int
    title: str
    icon: str


def badges_for_coins(coins: int) -> list[Badge]:
    """Все полученные бейджи по текущим монетам (уровню)."""
    li = level_by_coins(coins or 0)
    got = []
    for lvl, (title, icon) in sorted(BADGE_BY_LEVEL.items()):
        if li.level >= lvl:
            got.append(Badge(level=lvl, title=title, icon=icon))
    return got


def newly_unlocked_badge(level_before: int, level_after: int) -> Badge | None:
    """Какой бейдж открылся при переходе уровня (если открылся)."""
    if level_after <= level_before:
        return None
    # ищем первый бейдж, чей порог пересекли
    unlocked_levels = [
        lvl for lvl in BADGE_BY_LEVEL.keys() if level_before < lvl <= level_after
    ]
    if not unlocked_levels:
        return None
    lvl = min(unlocked_levels)
    title, icon = BADGE_BY_LEVEL[lvl]
    return Badge(level=lvl, title=title, icon=icon)


def render_badges_line(coins: int) -> str:
    """Короткая строка для профиля."""
    got = badges_for_coins(coins)
    if not got:
        return "—"
    return " ".join([b.icon for b in got]) + "  " + ", ".join([b.title for b in got])
