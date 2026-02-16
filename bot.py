import asyncio
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import (
    BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH,
    WEBAPP_HOST, WEBAPP_PORT
)
from database import init_db
from handlers import start_router, surveys_router, admin_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    await init_db()
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook set: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logger.info("Webhook deleted")


def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(surveys_router)
    dp.include_router(admin_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)


if __name__ == "__main__":
    main()