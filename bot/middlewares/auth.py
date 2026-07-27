from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from database.db import async_session_maker
from database.crud import is_user_allowed


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        telegram_id = user.id

        # Skip check for /start commands (so users can register via invite links)
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)

        async with async_session_maker() as session:
            allowed = await is_user_allowed(session, telegram_id)

        if not allowed:
            msg = "⛔ <b>Доступ ограничен</b>\n\nДля использования бота вам необходимо вступить по специальной ссылке-приглашению."
            if isinstance(event, Message):
                await event.answer(msg, parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                await event.answer("Доступ ограничен", show_alert=True)
            return

        return await handler(event, data)
