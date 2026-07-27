from aiogram import Router
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message
from database.db import async_session_maker
from database.crud import get_or_create_user, validate_and_use_access_link, is_user_allowed, set_user_allowed
from bot.keyboards.reply import get_main_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    deep_link_args = command.args

    async with async_session_maker() as session:
        invited_by = None
        if deep_link_args:
            valid_link = await validate_and_use_access_link(session, deep_link_args)
            if valid_link:
                invited_by = 0

        user = await get_or_create_user(
            session=session,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            invited_by=invited_by
        )

        if deep_link_args and not user.is_allowed:
            valid_link = await validate_and_use_access_link(session, deep_link_args)
            if valid_link:
                await set_user_allowed(session, telegram_id, True)
                user.is_allowed = True

        if not user.is_allowed:
            await message.answer(
                "⛔ <b>Доступ ограничен</b>\n\n"
                "Этот бот работает по пригласительным ссылкам.\n"
                "Перейдите по специальной реферальной ссылке для активации доступа."
            )
            return

    text = (
        f"👋 <b>Привет, {first_name or 'друг'}!</b>\n\n"
        "Я твой 🤖 <b>AI-ассистент по учету финансов</b> в сумах (UZS) и долларах ($).\n\n"
        "💡 <b>Как мной пользоваться:</b>\n"
        "1. <b>Просто отправляй мне текст</b> о любых тратах или доходах:\n"
        "   • <i>«Купил продукты на 145 000 сум»</i>\n"
        "   • <i>«Вчера сходил в ресторан на $35»</i>\n"
        "   • <i>«Получил аванс 4 500 000 сум»</i>\n"
        "   • <i>«Кофе 25000 сум»</i>\n\n"
        "2. <b>Отправляй фото чека</b> — я сам распознаю сумму и конвертирую по курсу ЦБ!\n\n"
        "3. <b>Смотри отчеты и графики:</b> нажимай кнопки меню ниже."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "ℹ️ <b>Справка по командам:</b>\n\n"
        "• Отправь текстовое сообщение или фото чека — бот автоматически распознает сумму в сумах и $.\n"
        "• 📊 <b>Недельный отчет</b> — сводка и диаграмма за 7 дней.\n"
        "• 📅 <b>Месячный отчет</b> — статистика за текущий месяц.\n"
        "• 📜 <b>История операций</b> — список последних трат.\n"
        "• 📥 <b>Экспорт в Excel</b> — выгрузить полную таблицу транзакций в сумах и $."
    )
    await message.answer(text, parse_mode="HTML")
