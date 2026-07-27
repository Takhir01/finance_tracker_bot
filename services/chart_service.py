import io
import matplotlib
matplotlib.use('Agg')  # Headless backend for server execution
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, Optional, Tuple


def generate_donut_chart(
    category_data: Dict[str, float],
    title: str = "Расходы по категориям",
    currency: str = "сум"
) -> Optional[io.BytesIO]:
    """Generates a modern donut pie chart for expenses by category."""
    if not category_data or sum(category_data.values()) <= 0:
        return None

    # Filter out 0 or negative values
    data = {k: v for k, v in category_data.items() if v > 0}
    if not data:
        return None

    labels = list(data.keys())
    values = list(data.values())
    total = sum(values)

    # Color palette
    colors = [
        "#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f",
        "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"
    ]
    if len(labels) > len(colors):
        # Extend palette if needed
        cmap = plt.get_cmap("tab20")
        colors = [cmap(i) for i in range(len(labels))]

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 7), dpi=150)
    fig.patch.set_facecolor('#1e1e2e')
    ax.set_facecolor('#1e1e2e')

    # Draw Donut Chart
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct=lambda pct: f'{pct:.1f}%\n({int(pct * total / 100):,} {currency})'.replace(',', ' '),
        startangle=140,
        pctdistance=0.78,
        colors=colors[:len(labels)],
        textprops=dict(color="#cdd6f4", fontsize=10, weight="bold"),
        wedgeprops=dict(width=0.4, edgecolor='#181825', linewidth=2)
    )

    # Center Text
    ax.text(
        0, 0,
        f"ИТОГО\n{total:,.0f} {currency}".replace(',', ' '),
        ha='center', va='center',
        fontsize=14, weight='bold', color='#ffffff'
    )

    ax.set_title(title, fontsize=16, weight='bold', color='#f5e0dc', pad=20)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_daily_bar_chart(
    daily_data: Dict[str, Dict[str, float]],
    title: str = "Динамика расходов и доходов",
    currency: str = "сум"
) -> Optional[io.BytesIO]:
    """Generates a bar chart showing daily expenses and income trends."""
    if not daily_data:
        return None

    days = sorted(list(daily_data.keys()))
    if not days:
        return None

    # Format short day labels (e.g. "27.07")
    short_days = [d.split("-")[1] + "." + d.split("-")[2] if "-" in d else d for d in days]
    expenses = [daily_data[d].get("expense", 0.0) for d in days]
    incomes = [daily_data[d].get("income", 0.0) for d in days]

    x = np.arange(len(days))
    width = 0.35

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    fig.patch.set_facecolor('#1e1e2e')
    ax.set_facecolor('#181825')

    rects1 = ax.bar(x - width/2, expenses, width, label='Расходы', color='#f38ba8', alpha=0.9, edgecolor='none')
    rects2 = ax.bar(x + width/2, incomes, width, label='Доходы', color='#a6e3a1', alpha=0.9, edgecolor='none')

    ax.set_ylabel(f'Сумма ({currency})', color='#cdd6f4', fontsize=12)
    ax.set_title(title, fontsize=15, weight='bold', color='#f5e0dc', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(short_days, rotation=45, ha='right', color='#cdd6f4', fontsize=9)
    ax.legend(facecolor='#1e1e2e', edgecolor='#313244', labelcolor='#cdd6f4')
    ax.grid(axis='y', linestyle='--', alpha=0.2, color='#6c7086')

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf
