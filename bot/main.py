"""Entry point. Webhook mode on Render (aiohttp server), long polling locally."""
from __future__ import annotations

import asyncio
import hmac
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from . import ai, config, db, scheduler
from .handlers import router
from .i18n import COMMANDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("planner")

WEBHOOK_PATH = "/webhook"
ALLOWED = ["message", "callback_query"]


def make_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp


async def set_commands(bot: Bot):
    for lang, cmds in COMMANDS.items():
        await bot.set_my_commands([BotCommand(command=c, description=d) for c, d in cmds],
                                  language_code=None if lang == "en" else lang)


async def _startup(bot: Bot):
    await db.connect()
    await set_commands(bot)


async def _shutdown(bot: Bot):
    await ai.close()
    await db.close()


def run_webhook():
    bot, dp = make_bot()
    tasks: list[asyncio.Task] = []

    async def on_startup(_app):
        await _startup(bot)
        await bot.set_webhook(f"{config.PUBLIC_URL}{WEBHOOK_PATH}", secret_token=config.WEBHOOK_SECRET or None,
                              allowed_updates=ALLOWED)
        tasks.append(asyncio.create_task(scheduler.loop(bot)))
        log.info("webhook set to %s%s", config.PUBLIC_URL, WEBHOOK_PATH)

    async def on_cleanup(_app):
        for tk in tasks:
            tk.cancel()
        await _shutdown(bot)
        await bot.session.close()

    async def health(_req):
        return web.Response(text="ok")

    async def tick(req: web.Request):
        # cron-job.org hits this every few minutes: keeps the free instance awake
        # and runs due work even if the in-process loop was frozen while asleep.
        # an unencoded "+" in the key (Render's generated values are base64) arrives as a space
        key = req.query.get("key", "").replace(" ", "+")
        if config.TICK_KEY and not hmac.compare_digest(key, config.TICK_KEY):
            return web.Response(status=403)
        await scheduler.tick(bot)
        return web.Response(text="ticked")

    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    app.router.add_get("/tick", tick)
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=config.WEBHOOK_SECRET or None).register(app, WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    web.run_app(app, host="0.0.0.0", port=config.PORT)


async def run_polling():
    bot, dp = make_bot()
    await _startup(bot)
    await bot.delete_webhook(drop_pending_updates=False)
    loop_task = asyncio.create_task(scheduler.loop(bot))
    try:
        await dp.start_polling(bot, allowed_updates=ALLOWED)
    finally:
        loop_task.cancel()
        await _shutdown(bot)


def main():
    missing = [k for k in ("BOT_TOKEN", "DATABASE_URL", "ENCRYPTION_KEY") if not getattr(config, k)]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)} (see .env.example)")
    if config.MODE == "webhook":
        run_webhook()
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
