# bot/services/levels.py
from dataclasses import dataclass

# Пороги по сумме coins (можно поменять позже)
# Level 1 = 0c, L2 = 10c, L3 = 25c, L4 = 50c, L5 = 100c, ...
LEVEL_THRESHOLDS = [0, 10, 25, 50, 100, 200, 400, 700, 1100, 1600]


@dataclass
class LevelInfo:
    level: int
    current_base: int
    next_base: int | None
    progress_percent: int
    to_next: int | None


def level_by_coins(coins: int) -> LevelInfo:
    coins = max(0, coins or 0)
    # найдём максимальный порог <= coins
    idx = 0
    for i, th in enumerate(LEVEL_THRESHOLDS):
        if coins >= th:
            idx = i
        else:
            break

    level = idx + 1  # индексация уровней с 1
    current_base = LEVEL_THRESHOLDS[idx]
    next_base = LEVEL_THRESHOLDS[idx + 1] if idx + 1 < len(LEVEL_THRESHOLDS) else None

    if next_base is None:
        return LevelInfo(
            level=level,
            current_base=current_base,
            next_base=None,
            progress_percent=100,
            to_next=None,
        )

    span = next_base - current_base
    done = coins - current_base
    percent = int(round(100 * done / span)) if span > 0 else 100
    to_next = max(0, next_base - coins)
    return LevelInfo(
        level=level,
        current_base=current_base,
        next_base=next_base,
        progress_percent=min(100, percent),
        to_next=to_next,
    )


def render_progress_bar(percent: int, width: int = 10) -> str:
    """Текстовая шкала прогресса: ▰▰▰▰▱▱▱▱▱▱"""
    filled = int(round(width * percent / 100))
    return "▰" * filled + "▱" * (width - filled)
