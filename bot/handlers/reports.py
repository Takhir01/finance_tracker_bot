from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from database.db import async_session_maker
from database.crud import get_period_summary, get_user_transactions
from services.report_service import format_text_report, export_transactions_to_excel
from services.chart_service import generate_donut_chart, generate_daily_bar_chart
from services.currency_service import get_usd_uzs_rate

router = Router()


@router.message(F.text.in_({"📊 Недельный отчет", "/weekly"}))
async def cmd_weekly_report(message: Message):
    user_id = message.from_user.id
    now = datetime.utcnow()
    start_date = now - timedelta(days=7)
    rate = await get_usd_uzs_rate()

    async with async_session_maker() as session:
        summary = await get_period_summary(session, user_id, start_date, now)

    report_text = format_text_report(summary, period_title="За последние 7 дней", usd_rate=rate)

    # Generate Donut chart for expenses in UZS
    donut_buf = generate_donut_chart(summary["expense_categories"], title="Расходы за неделю", currency="сум")
    if donut_buf:
        photo = BufferedInputFile(donut_buf.getvalue(), filename="weekly_expenses.png")
        await message.answer_photo(photo, caption=report_text, parse_mode="HTML")
    else:
        await message.answer(report_text, parse_mode="HTML")

    # Generate daily dynamics chart if there are entries
    if summary["daily_data"]:
        bar_buf = generate_daily_bar_chart(summary["daily_data"], title="Динамика за неделю", currency="сум")
        if bar_buf:
            photo_bar = BufferedInputFile(bar_buf.getvalue(), filename="weekly_trends.png")
            await message.answer_photo(photo_bar, caption="📈 <b>Динамика трат и доходов по дням</b>", parse_mode="HTML")


@router.message(F.text.in_({"📅 Месячный отчет", "/monthly"}))
async def cmd_monthly_report(message: Message):
    user_id = message.from_user.id
    now = datetime.utcnow()
    start_date = datetime(now.year, now.month, 1)
    rate = await get_usd_uzs_rate()

    async with async_session_maker() as session:
        summary = await get_period_summary(session, user_id, start_date, now)

    month_name_ru = [
        "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ][now.month]

    report_text = format_text_report(summary, period_title=f"{month_name_ru} {now.year}", usd_rate=rate)

    # Generate Donut chart for expenses in UZS
    donut_buf = generate_donut_chart(summary["expense_categories"], title=f"Расходы за {month_name_ru}", currency="сум")
    if donut_buf:
        photo = BufferedInputFile(donut_buf.getvalue(), filename="monthly_expenses.png")
        await message.answer_photo(photo, caption=report_text, parse_mode="HTML")
    else:
        await message.answer(report_text, parse_mode="HTML")

    # Generate daily trend bar chart
    if summary["daily_data"]:
        bar_buf = generate_daily_bar_chart(summary["daily_data"], title=f"Динамика за {month_name_ru}", currency="сум")
        if bar_buf:
            photo_bar = BufferedInputFile(bar_buf.getvalue(), filename="monthly_trends.png")
            await message.answer_photo(photo_bar, caption="📈 <b>Динамика расходов и доходов по дням</b>", parse_mode="HTML")


@router.message(F.text.in_({"📜 История операций", "/history"}))
async def cmd_history(message: Message):
    user_id = message.from_user.id
    rate = await get_usd_uzs_rate()

    async with async_session_maker() as session:
        transactions = await get_user_transactions(session, user_id, limit=15)

    if not transactions:
        await message.answer("📜 <b>У вас пока нет сохраненных операций.</b>", parse_mode="HTML")
        return

    lines = ["📜 <b>Последние 15 операций:</b>\n"]
    for tx in transactions:
        icon = "🔴" if tx.type == "expense" else "🟢"
        date_str = tx.date.strftime("%d.%m %H:%M") if tx.date else ""
        desc = f" ({tx.description})" if tx.description else ""
        amount_usd = tx.amount / rate if rate > 0 else 0.0
        lines.append(f"{icon} <b>{tx.amount:,.0f} сум (${amount_usd:,.2f})</b> | {tx.category}{desc} — <i>{date_str}</i>".replace(',', ' '))

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(F.text.in_({"📥 Экспорт в Excel", "/export"}))
async def cmd_export_excel(message: Message):
    user_id = message.from_user.id
    msg_status = await message.answer("⏳ <i>Формирую Excel отчет...</i>", parse_mode="HTML")
    rate = await get_usd_uzs_rate()

    async with async_session_maker() as session:
        transactions = await get_user_transactions(session, user_id, limit=5000)

    if not transactions:
        await msg_status.edit_text("ℹ️ Нет операций для экспорта.")
        return

    excel_buf = export_transactions_to_excel(transactions, usd_rate=rate)
    doc = BufferedInputFile(excel_buf.getvalue(), filename=f"finance_report_{user_id}.xlsx")
    await message.answer_document(doc, caption="📊 <b>Ваш полный отчет по финансовым операциям в формате Excel (сум и $).</b>", parse_mode="HTML")
    await msg_status.delete()
