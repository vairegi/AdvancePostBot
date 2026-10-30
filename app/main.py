import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.config import (
    BOT_TOKEN,
    RENDER_EXTERNAL_URL,
    WEBHOOK_SECRET,
    PORT,
    WEBHOOK_PATH,
    HEALTH_PATH,
)
from app import db
from app.handlers import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("post-creator-bot")


async def on_startup(bot: Bot):
    await db.init_indexes()

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Open the main menu"),
            BotCommand(command="help", description="How to use the bot"),
        ]
    )

    if RENDER_EXTERNAL_URL:
        webhook_url = RENDER_EXTERNAL_URL + WEBHOOK_PATH

        await bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )

        logger.info("Webhook set: %s", webhook_url)
    else:
        logger.warning("RENDER_EXTERNAL_URL missing; webhook not set.")


async def health(request):
    return web.json_response(
        {
            "status": "ok",
            "service": "telegram-post-creator-bot",
        }
    )


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    dispatcher.startup.register(on_startup)

    app = web.Application()
    app.router.add_get(HEALTH_PATH, health)

    webhook_handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )

    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    setup_application(app, dispatcher, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=PORT,
    )
    await site.start()

    logger.info("HTTP server running on port %s", PORT)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())