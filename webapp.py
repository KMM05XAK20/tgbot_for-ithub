
import os, asyncio
from flask import Flask, request, abort
from aiogram.types import Update
from bot.config import get_settings
from bot.app_factory import build_dispatcher

settings = get_settings()
bot, dp = build_dispatcher(settings.bot_token)

# Защитим URL секретом, чтобы никто посторонний не дергал
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret")

app = Flask(__name__)

@app.post(f"/webhook/{WEBHOOK_SECRET}")
def telegram_webhook():
    if not request.data:
        abort(400)
    try:
        update = Update.model_validate_json(request.data)
    except Exception:
        abort(400)
    # Внутри WSGI-процесса запускаем разовый event-loop на обработку апдейта
    asyncio.run(dp.feed_update(bot, update))
    return "ok"
