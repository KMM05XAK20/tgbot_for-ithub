import os, asyncio
from bot.config import get_settings
from bot.app_factory import build_dispatcher

async def main():
    settings = get_settings()
    bot, _ = build_dispatcher(settings.bot_token)
    base = os.environ["PA_BASE_URL"].rstrip("/")  # например: https://<твое_имя>.pythonanywhere.com
    secret = os.environ.get("WEBHOOK_SECRET", "supersecret")
    url = f"{base}/webhook/{secret}"
    await bot.set_webhook(url)
    print("Webhook set to:", url)

if __name__ == "__main__":
    asyncio.run(main())
