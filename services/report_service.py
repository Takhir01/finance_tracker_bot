import io
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from database.models import Transaction


def format_text_report(summary: Dict[str, Any], period_title: str, usd_rate: float = 12850.0) -> str:
    """Formats period summary into clear Markdown message with UZS (сум) and USD ($)."""
    total_exp = summary["total_expense"]
    total_inc = summary["total_income"]
    net = summary["net_balance"]
    exp_cats = summary["expense_categories"]
    inc_cats = summary["income_categories"]

    total_exp_usd = total_exp / usd_rate if usd_rate > 0 else 0
    total_inc_usd = total_inc / usd_rate if usd_rate > 0 else 0
    net_usd = net / usd_rate if usd_rate > 0 else 0

    lines = []
    lines.append(f"📊 <b>Отчет по финансам: {period_title}</b>")
    lines.append(f"💱 <i>Курс ЦБ: 1 USD = {usd_rate:,.2f} сум</i>\n".replace(',', ' '))

    lines.append(f"🔴 <b>Всего расходов:</b> {total_exp:,.0f} сум <b>(${total_exp_usd:,.2f})</b>".replace(',', ' '))
    lines.append(f"🟢 <b>Всего доходов:</b> {total_inc:,.0f} сум <b>(${total_inc_usd:,.2f})</b>".replace(',', ' '))

    balance_icon = "🟢" if net >= 0 else "🔴"
    lines.append(f"{balance_icon} <b>Итоговый баланс:</b> {net:,.0f} сум <b>(${net_usd:,.2f})</b>\n".replace(',', ' '))

    if exp_cats:
        lines.append("🔻 <b>Расходы по категориям:</b>")
        for cat, amount in exp_cats.items():
            pct = (amount / total_exp * 100) if total_exp > 0 else 0
            cat_usd = amount / usd_rate if usd_rate > 0 else 0
            lines.append(f"  • {cat}: <b>{amount:,.0f} сум</b> (${cat_usd:,.2f}) — <i>{pct:.1f}%</i>".replace(',', ' '))
        lines.append("")

    if inc_cats:
        lines.append("🔺 <b>Доходы по категориям:</b>")
        for cat, amount in inc_cats.items():
            pct = (amount / total_inc * 100) if total_inc > 0 else 0
            cat_usd = amount / usd_rate if usd_rate > 0 else 0
            lines.append(f"  • {cat}: <b>{amount:,.0f} сум</b> (${cat_usd:,.2f}) — <i>{pct:.1f}%</i>".replace(',', ' '))

    if not exp_cats and not inc_cats:
        lines.append("ℹ️ За выбранный период операций не найдено.")

    return "\n".join(lines)


def export_transactions_to_excel(transactions: List[Transaction], usd_rate: float = 12850.0) -> io.BytesIO:
    """Exports list of transactions to Excel buffer with both UZS and USD columns."""
    data = []
    for tx in transactions:
        amount_usd = tx.amount / usd_rate if usd_rate > 0 else 0.0
        data.append({
            "ID": tx.id,
            "Дата": tx.date.strftime("%Y-%m-%d %H:%M:%S") if tx.date else "",
            "Тип": "Расход" if tx.type == "expense" else "Доход",
            "Сумма (сум)": tx.amount,
            "Сумма ($ USD)": round(amount_usd, 2),
            "Категория": tx.category,
            "Описание": tx.description or "",
            "Исходный текст": tx.raw_text or ""
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Транзакции')

    output.seek(0)
    return output
