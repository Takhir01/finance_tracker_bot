from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="📊 Недельный отчет"),
            KeyboardButton(text="📅 Месячный отчет")
        ],
        [
            KeyboardButton(text="📜 История операций"),
            KeyboardButton(text="📥 Экспорт в Excel")
        ],
        [
            KeyboardButton(text="🏷 Категории"),
            KeyboardButton(text="🔗 Получить ссылку доступа")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        persistent=True
    )
