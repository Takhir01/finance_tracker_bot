import asyncio
import os
import sys
from datetime import datetime, timedelta

# Append current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db, async_session_maker
from database.crud import get_or_create_user, add_transaction, get_period_summary
from services.gemini_service import GeminiService
from services.chart_service import generate_donut_chart, generate_daily_bar_chart
from services.report_service import format_text_report


async def run_tests():
    print("1. Initializing DB...")
    await init_db()

    async with async_session_maker() as session:
        user = await get_or_create_user(session, telegram_id=99999, username="testuser", first_name="Test")
        print(f"User created: {user.telegram_id}")

        print("2. Adding test transactions...")
        await add_transaction(session, user_id=99999, tx_type="expense", amount=450.0, category="Напитки", description="Кофе и тост")
        await add_transaction(session, user_id=99999, tx_type="expense", amount=3500.0, category="Продукты", description="Покупка продуктов")
        await add_transaction(session, user_id=99999, tx_type="expense", amount=5000.0, category="Подарки", description="Подарок на день рождения")
        await add_transaction(session, user_id=99999, tx_type="income", amount=50000.0, category="Доходы", description="Аванс за проект")

        now = datetime.utcnow()
        summary = await get_period_summary(session, user_id=99999, start_date=now - timedelta(days=7), end_date=now)
        print(f"Summary calculated: Expense={summary['total_expense']}, Income={summary['total_income']}")

    print("3. Testing Gemini API Text Parser...")
    gemini = GeminiService()
    parsed = await gemini.parse_text_transaction("купил подарки на день рождения подруге на 2500 рублей")
    print(f"Gemini Parsed Result: Type={parsed.type}, Amount={parsed.amount}, Cat={parsed.category}, Desc={parsed.description}")

    print("4. Testing Chart Generation...")
    donut_buf = generate_donut_chart(summary["expense_categories"], title="Тестовые расходы")
    assert donut_buf is not None, "Donut chart generation failed!"
    print("Donut chart generated successfully!")

    bar_buf = generate_daily_bar_chart(summary["daily_data"], title="Тестовая динамика")
    assert bar_buf is not None, "Bar chart generation failed!"
    print("Bar chart generated successfully!")

    report_text = format_text_report(summary, "Тестовый период")
    print("\n--- Formatted Text Report Sample ---")
    print(report_text)
    print("-----------------------------------")

    print("✅ All verification tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(run_tests())
