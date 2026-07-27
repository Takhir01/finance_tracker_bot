from aiogram import Router, F
from aiogram.types import Message
from services.gemini_service import DEFAULT_CATEGORIES

router = Router()


@router.message(F.text.in_({"🏷 Категории", "/categories"}))
async def cmd_categories(message: Message):
    cats_text = "\n".join([f"  • {cat}" for cat in DEFAULT_CATEGORIES])
    text = (
        "🏷 <b>Категории расходов и доходов:</b>\n\n"
        f"{cats_text}\n\n"
        "💡 <i>При отправке сообщения Gemini AI автоматически подбирает наиболее подходящую категорию или вы можете сменить ее в 1 клик через кнопки.</i>"
    )
    await message.answer(text, parse_mode="HTML")
