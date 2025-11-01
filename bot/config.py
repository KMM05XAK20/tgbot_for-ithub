from dataclasses import dataclass
import os
from dotenv import load_dotenv

@dataclass
class Setting:
    bot_token: str
    admin_ids: list[str]

def get_settings() -> Setting:
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT TOKEN не найден в .env")
    
    raw_admins = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(x) for x in raw_admins.split(",") if x.strip().isdigit()]
    return Setting(bot_token=token, admin_ids=admin_ids)