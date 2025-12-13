from dataclasses import dataclass
import os
import redis
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class Setting:
    redis_cli = redis.StrictRedis(
        host="localhost", port=6379, db=0, decode_responses=True
    )
    bot_token: str
    admin_ids: list[str]
    use_webhook: bool = False


def get_settings() -> Setting:
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT TOKEN не найден в .env")

    raw_admins = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(x) for x in raw_admins.split(",") if x.strip().isdigit()]
    use_webhook = os.getenv("USE_WEBHOOK", "false").lower() == "true"
    return Setting(bot_token=token, admin_ids=admin_ids, use_webhook=use_webhook)
