import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database.db import async_session_maker
from database.crud import add_transaction, get_transaction, update_transaction, delete_transaction
from services.gemini_service import GeminiService
from services.currency_service import get_usd_uzs_rate, convert_uzs_to_usd
from bot.keyboards.inline import get_tx_confirm_keyboard, get_category_select_keyboard

logger = logging.getLogger(__name__)
router = Router()

_gemini_instance: Optional[GeminiService] = None


def get_gemini() -> GeminiService:
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = GeminiService()
    return _gemini_instance


RECEIPTS_DIR = "downloads/receipts"
os.makedirs(RECEIPTS_DIR, exist_ok=True)


def format_amount_display(amount_uzs: float, usd_rate: float) -> str:
    amount_usd = amount_uzs / usd_rate if usd_rate > 0 else 0.0
    return f"<code>{amount_uzs:,.0f} сум</code> <b>(${amount_usd:,.2f})</b>".replace(',', ' ')


@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_transaction(message: Message):
    if message.text in ["📊 Недельный отчет", "📅 Месячный отчет", "📜 История операций", "📥 Экспорт в Excel", "🏷 Категории", "🔗 Получить ссылку доступа"]:
        return

    msg_status = await message.answer("🧠 <i>Анализирую операцию...</i>", parse_mode="HTML")
    try:
        gemini = get_gemini()
        parsed = await gemini.parse_text_transaction(message.text)
        rate = await get_usd_uzs_rate()
    except Exception as e:
        logger.error(f"Error parsing transaction: {e}")
        await msg_status.edit_text("❌ Не удалось распознать операцию. Попробуйте написать точнее, например: <i>«Кофе 25000 сум»</i> или <i>«Такси $5»</i>.", parse_mode="HTML")
        return

    # If amount was in USD, convert to UZS for DB storage
    if parsed.currency == "USD":
        amount_uzs = parsed.amount * rate
    else:
        amount_uzs = parsed.amount

    tx_date = datetime.utcnow() + timedelta(days=parsed.date_offset_days)

    async with async_session_maker() as session:
        tx = await add_transaction(
            session=session,
            user_id=message.from_user.id,
            tx_type=parsed.type,
            amount=amount_uzs,
            category=parsed.category,
            description=parsed.description,
            raw_text=message.text,
            date=tx_date
        )

    icon = "🔴 Расход" if tx.type == "expense" else "🟢 Доход"
    amount_str = format_amount_display(tx.amount, rate)

    text = (
        f"✅ <b>Операция распознана!</b>\n\n"
        f"<b>Тип:</b> {icon}\n"
        f"<b>Сумма:</b> {amount_str}\n"
        f"<b>Категория:</b> {tx.category}\n"
        f"<b>Описание:</b> {tx.description or '—'}\n"
        f"<b>Курс ЦБ:</b> 1 USD = {rate:,.0f} сум\n".replace(',', ' ') +
        f"<b>Дата:</b> {tx.date.strftime('%Y-%m-%d %H:%M')}\n"
    )
    await msg_status.edit_text(text, parse_mode="HTML", reply_markup=get_tx_confirm_keyboard(tx.id, tx.type))


@router.message(F.photo)
async def handle_photo_receipt(message: Message):
    msg_status = await message.answer("📸 <i>Сканирую чек и анализирую...</i>", parse_mode="HTML")

    photo = message.photo[-1]
    file_path = os.path.join(RECEIPTS_DIR, f"{message.from_user.id}_{photo.file_unique_id}.jpg")
    await message.bot.download(photo, destination=file_path)

    caption = message.caption or ""
    try:
        gemini = get_gemini()
        parsed = await gemini.parse_receipt_photo(file_path, user_comment=caption)
        rate = await get_usd_uzs_rate()
    except Exception as e:
        logger.error(f"Error parsing receipt photo: {e}")
        await msg_status.edit_text("❌ Не удалось распознать чек на фотографии. Проверьте четкость изображения.", parse_mode="HTML")
        return

    if parsed.currency == "USD":
        amount_uzs = parsed.amount * rate
    else:
        amount_uzs = parsed.amount

    tx_date = datetime.utcnow() + timedelta(days=parsed.date_offset_days)

    async with async_session_maker() as session:
        tx = await add_transaction(
            session=session,
            user_id=message.from_user.id,
            tx_type=parsed.type,
            amount=amount_uzs,
            category=parsed.category,
            description=parsed.description,
            raw_text=caption or "Чек с фото",
            receipt_path=file_path,
            date=tx_date
        )

    icon = "🔴 Расход" if tx.type == "expense" else "🟢 Доход"
    amount_str = format_amount_display(tx.amount, rate)

    text = (
        f"🧾 <b>Чек успешно распознан!</b>\n\n"
        f"<b>Тип:</b> {icon}\n"
        f"<b>Сумма:</b> {amount_str}\n"
        f"<b>Категория:</b> {tx.category}\n"
        f"<b>Описание:</b> {tx.description or '—'}\n"
        f"<b>Дата:</b> {tx.date.strftime('%Y-%m-%d %H:%M')}\n"
    )
    await msg_status.edit_text(text, parse_mode="HTML", reply_markup=get_tx_confirm_keyboard(tx.id, tx.type))


@router.message(F.voice)
async def handle_voice_transaction(message: Message):
    msg_status = await message.answer("🎙 <i>Слушаю и распознаю голосовое сообщение...</i>", parse_mode="HTML")

    voice = message.voice
    file_info = await message.bot.get_file(voice.file_id)
    downloaded_file = await message.bot.download_file(file_info.file_path)
    audio_bytes = downloaded_file.read()

    try:
        gemini = get_gemini()
        parsed = await gemini.parse_voice_transaction(audio_bytes, mime_type="audio/ogg")
        rate = await get_usd_uzs_rate()
    except Exception as e:
        logger.error(f"Error parsing voice transaction: {e}")
        await msg_status.edit_text("❌ Не удалось распознать голосовое сообщение. Попробуйте надиктовать отчетливее.", parse_mode="HTML")
        return

    if parsed.currency == "USD":
        amount_uzs = parsed.amount * rate
    else:
        amount_uzs = parsed.amount

    tx_date = datetime.utcnow() + timedelta(days=parsed.date_offset_days)

    async with async_session_maker() as session:
        tx = await add_transaction(
            session=session,
            user_id=message.from_user.id,
            tx_type=parsed.type,
            amount=amount_uzs,
            category=parsed.category,
            description=parsed.description,
            raw_text="Голосовое сообщение",
            date=tx_date
        )

    icon = "🔴 Расход" if tx.type == "expense" else "🟢 Доход"
    amount_str = format_amount_display(tx.amount, rate)

    text = (
        f"🎙 <b>Голосовая операция распознана!</b>\n\n"
        f"<b>Тип:</b> {icon}\n"
        f"<b>Сумма:</b> {amount_str}\n"
        f"<b>Категория:</b> {tx.category}\n"
        f"<b>Описание:</b> {tx.description or '—'}\n"
        f"<b>Курс ЦБ:</b> 1 USD = {rate:,.0f} сум\n".replace(',', ' ') +
        f"<b>Дата:</b> {tx.date.strftime('%Y-%m-%d %H:%M')}\n"
    )
    await msg_status.edit_text(text, parse_mode="HTML", reply_markup=get_tx_confirm_keyboard(tx.id, tx.type))



@router.callback_query(F.data.startswith("tx_confirm:"))
async def callback_confirm_tx(callback: CallbackQuery):
    tx_id = int(callback.data.split(":")[1])
    rate = await get_usd_uzs_rate()
    async with async_session_maker() as session:
        tx = await get_transaction(session, tx_id)
        if tx:
            await callback.answer("Сохранено!", show_alert=False)
            icon = "🔴 Расход" if tx.type == "expense" else "🟢 Доход"
            amount_str = format_amount_display(tx.amount, rate)
            text = (
                f"💾 <b>Запись сохранена в базу!</b>\n\n"
                f"<b>Тип:</b> {icon}\n"
                f"<b>Сумма:</b> {amount_str}\n"
                f"<b>Категория:</b> {tx.category}\n"
                f"<b>Описание:</b> {tx.description or '—'}"
            )
            await callback.message.edit_text(text, parse_mode="HTML")
        else:
            await callback.answer("Операция не найдена", show_alert=True)


@router.callback_query(F.data.startswith("tx_toggle_type:"))
async def callback_toggle_type(callback: CallbackQuery):
    tx_id = int(callback.data.split(":")[1])
    rate = await get_usd_uzs_rate()
    async with async_session_maker() as session:
        tx = await get_transaction(session, tx_id)
        if tx:
            new_type = "income" if tx.type == "expense" else "expense"
            new_cat = "Доходы" if new_type == "income" else "Продукты"
            tx = await update_transaction(session, tx_id, type=new_type, category=new_cat)
            await callback.answer(f"Тип изменен на {'Доход' if new_type == 'income' else 'Расход'}")

            icon = "🔴 Расход" if tx.type == "expense" else "🟢 Доход"
            amount_str = format_amount_display(tx.amount, rate)
            text = (
                f"✅ <b>Операция обновлена!</b>\n\n"
                f"<b>Тип:</b> {icon}\n"
                f"<b>Сумма:</b> {amount_str}\n"
                f"<b>Категория:</b> {tx.category}\n"
                f"<b>Описание:</b> {tx.description or '—'}\n"
                f"<b>Дата:</b> {tx.date.strftime('%Y-%m-%d %H:%M')}\n"
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_tx_confirm_keyboard(tx.id, tx.type))


@router.callback_query(F.data.startswith("tx_edit_cat:"))
async def callback_edit_cat(callback: CallbackQuery):
    tx_id = int(callback.data.split(":")[1])
    await callback.message.edit_text("Выберите нужную категорию:", reply_markup=get_category_select_keyboard(tx_id))


@router.callback_query(F.data.startswith("tx_set_cat:"))
async def callback_set_cat(callback: CallbackQuery):
    parts = callback.data.split(":")
    tx_id = int(parts[1])
    cat_name = parts[2]
    rate = await get_usd_uzs_rate()

    async with async_session_maker() as session:
        tx = await update_transaction(session, tx_id, category=cat_name)
        if tx:
            await callback.answer(f"Категория: {cat_name}")
            icon = "🔴 Расход" if tx.type == "expense" else "🟢 Доход"
            amount_str = format_amount_display(tx.amount, rate)
            text = (
                f"✅ <b>Операция обновлена!</b>\n\n"
                f"<b>Тип:</b> {icon}\n"
                f"<b>Сумма:</b> {amount_str}\n"
                f"<b>Категория:</b> {tx.category}\n"
                f"<b>Описание:</b> {tx.description or '—'}\n"
                f"<b>Дата:</b> {tx.date.strftime('%Y-%m-%d %H:%M')}\n"
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_tx_confirm_keyboard(tx.id, tx.type))


@router.callback_query(F.data.startswith("tx_back:"))
async def callback_back(callback: CallbackQuery):
    tx_id = int(callback.data.split(":")[1])
    rate = await get_usd_uzs_rate()
    async with async_session_maker() as session:
        tx = await get_transaction(session, tx_id)
        if tx:
            icon = "🔴 Расход" if tx.type == "expense" else "🟢 Доход"
            amount_str = format_amount_display(tx.amount, rate)
            text = (
                f"✅ <b>Детали операции:</b>\n\n"
                f"<b>Тип:</b> {icon}\n"
                f"<b>Сумма:</b> {amount_str}\n"
                f"<b>Категория:</b> {tx.category}\n"
                f"<b>Описание:</b> {tx.description or '—'}\n"
            )
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_tx_confirm_keyboard(tx.id, tx.type))


@router.callback_query(F.data.startswith("tx_delete:"))
async def callback_delete(callback: CallbackQuery):
    tx_id = int(callback.data.split(":")[1])
    async with async_session_maker() as session:
        await delete_transaction(session, tx_id)
    await callback.answer("Операция удалена", show_alert=True)
    await callback.message.edit_text("🗑 <b>Операция удалена.</b>", parse_mode="HTML")
