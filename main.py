import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import settings
from database.db import init_db
from bot.middlewares.auth import AuthMiddleware
from bot.handlers import start, transaction, reports, categories, admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


async def main():
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN missing in .env file! Please insert your Telegram Bot Token from @BotFather.")
        print("\n" + "="*70)
        print(" ОШИБКА: Пожалуйста, откройте файл .env и укажите ваш BOT_TOKEN от @BotFather!")
        print("="*70 + "\n")
        sys.exit(1)

    logger.info("Initializing database...")
    await init_db()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    # Register authentication middleware
    dp.message.outer_middleware(AuthMiddleware())
    dp.callback_query.outer_middleware(AuthMiddleware())

    # Include routers
    dp.include_router(start.router)
    dp.include_router(reports.router)
    dp.include_router(categories.router)
    dp.include_router(admin.router)
    dp.include_router(transaction.router)

    logger.info("🚀 AI Finance Tracker Bot successfully started polling!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
