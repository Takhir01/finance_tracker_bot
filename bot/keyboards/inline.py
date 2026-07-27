from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from services.gemini_service import DEFAULT_CATEGORIES


def get_tx_confirm_keyboard(tx_id: int, current_type: str) -> InlineKeyboardMarkup:
    type_label = "🔴 Расход" if current_type == "expense" else "🟢 Доход"
    switch_label = "➡️ Переключить на Доход" if current_type == "expense" else "➡️ Переключить на Расход"

    buttons = [
        [
            InlineKeyboardButton(text="✅ Сохранить", callback_data=f"tx_confirm:{tx_id}")
        ],
        [
            InlineKeyboardButton(text="🏷 Выбрать категорию", callback_data=f"tx_edit_cat:{tx_id}"),
            InlineKeyboardButton(text=switch_label, callback_data=f"tx_toggle_type:{tx_id}")
        ],
        [
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"tx_delete:{tx_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_category_select_keyboard(tx_id: int) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for cat in DEFAULT_CATEGORIES:
        row.append(InlineKeyboardButton(text=cat, callback_data=f"tx_set_cat:{tx_id}:{cat}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"tx_back:{tx_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tx_delete_keyboard(tx_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="❌ Удалить запись", callback_data=f"tx_del_confirm:{tx_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
