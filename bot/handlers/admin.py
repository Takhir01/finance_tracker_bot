import uuid
from aiogram import Router, F
from aiogram.types import Message
from database.db import async_session_maker
from database.crud import create_access_link, get_bot_stats
from config import settings

router = Router()


@router.message(F.text.in_({"🔗 Получить ссылку доступа", "/genlink"}))
async def cmd_gen_link(message: Message):
    user_id = message.from_user.id
    code = str(uuid.uuid4())[:8]

    async with async_session_maker() as session:
        await create_access_link(session, created_by=user_id, code=code, max_uses=-1)

    bot_info = await message.bot.get_me()
    invite_url = f"https://t.me/{bot_info.username}?start={code}"

    text = (
        "🔗 <b>Пригласительная ссылка для доступа:</b>\n\n"
        f"<code>{invite_url}</code>\n\n"
        "Отправьте эту ссылку друзьям или клиентам. По ней они смогут зарегистрироваться и свободно пользоваться ботом!"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text.in_({"👥 Статистика", "/stats", "/admin_stats"}))
async def cmd_bot_stats(message: Message):
    async with async_session_maker() as session:
        stats = await get_bot_stats(session)

    text = (
        "📊 <b>Статистика использования бота</b>\n\n"
        "👥 <b>Пользователи:</b>\n"
        f"• Всего зарегистрировано: <b>{stats['total_users']}</b>\n"
        f"• Доступ разрешен: <b>{stats['allowed_users']}</b>\n"
        f"• Новых за сегодня: <b>{stats['today_users']}</b>\n"
        f"• Активных (ведут учет): <b>{stats['active_users']}</b>\n\n"
        "💳 <b>Активность и ресурсы:</b>\n"
        f"• Всего транзакций: <b>{stats['total_transactions']}</b>\n"
        f"• Создано инвайт-ссылок: <b>{stats['total_links']}</b>"
    )
    await message.answer(text, parse_mode="HTML")

