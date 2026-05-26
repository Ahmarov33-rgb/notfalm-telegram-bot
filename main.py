import asyncio
import logging
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from handlers import main as main_handler
from handlers import orders as orders_handler
from handlers import admin as admin_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def internal_notify_handler(request: web.Request) -> web.Response:
    """Internal webhook for backend to notify admins about new orders"""
    bot: Bot = request.app["bot"]
    data = await request.json()

    order_id = data.get("order_id")
    user_tg = data.get("user_telegram_id")
    total = data.get("total_amount", 0)

    for admin_id in settings.admin_ids_list:
        try:
            await bot.send_message(
                admin_id,
                f"💰 <b>Новая заявка на оплату!</b>\n\n"
                f"Заказ: <b>#{order_id}</b>\n"
                f"Telegram ID покупателя: <code>{user_tg}</code>\n"
                f"Сумма: <b>{total}₽</b>\n\n"
                f"Откройте /admin → Заказы для подтверждения.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Failed to notify admin {admin_id}: {e}")

    return web.json_response({"ok": True})


async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register all routers
    dp.include_router(admin_handler.router)
    dp.include_router(orders_handler.router)
    dp.include_router(main_handler.router)

    # Internal HTTP server for backend notifications
    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/notify/new_order", internal_notify_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8001)
    await site.start()
    logger.info("Internal notification server started on port 8001")

    # Start polling
    logger.info("Starting NOTFALM SHOP bot...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
