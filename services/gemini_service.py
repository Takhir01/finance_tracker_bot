import json
import logging
from typing import Optional, Dict, Any, Union
from PIL import Image
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from config import settings

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = [
    "Продукты",
    "Напитки",
    "День рождения",
    "Подарки",
    "Развлечения",
    "Кафе и рестораны",
    "Транспорт",
    "Жилье и ЖКХ",
    "Здоровье и аптека",
    "Одежда и шопинг",
    "Техника",
    "Доходы",
    "Разное"
]


class ParsedTransaction(BaseModel):
    type: str = Field(
        description="Must be either 'expense' (расход) or 'income' (доход)"
    )
    amount: float = Field(
        description="Numeric amount of transaction."
    )
    currency: str = Field(
        default="UZS",
        description="Currency code: 'USD' if user explicitly wrote $, usd, долларов, иначе 'UZS' (сумы)."
    )
    category: str = Field(
        description=f"Best fitting category from: {', '.join(DEFAULT_CATEGORIES)}. Create new clean Russian category if none fits."
    )
    description: str = Field(
        description="Short description of what was purchased or source of income"
    )
    date_offset_days: int = Field(
        default=0,
        description="Offset in days relative to current date (0 = today, -1 = yesterday, -2 = day before yesterday, etc.)"
    )


class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or settings.GEMINI_API_KEY
        if not key:
            raise ValueError("GEMINI_API_KEY is missing!")
        self.client = genai.Client(api_key=key)
        self.model_name = "gemini-2.0-flash"

    async def parse_text_transaction(self, text: str) -> ParsedTransaction:
        """Parses text message into structured financial transaction in UZS or USD."""
        prompt = f"""
Ты — финансовый ассистент по учету расходов и доходов в Узбекистане (валюта — узбекские сумы UZS и доллары USD).
Проанализируй текст сообщения пользователя и выдели детали финансовой операции.

Существующие категории: {', '.join(DEFAULT_CATEGORIES)}.
Правила:
1. Определи тип операции: 'expense' (расход, трата, покупка) или 'income' (доход, зарплата, перевод мне, аванс).
2. Выдели итоговую сумму в числах.
3. Валюта: Если указаны $, usd, доллар, баксов — установи currency = "USD". Во всех остальных случаях currency = "UZS" (сумы).
4. Подбери наилучшую категорию из списка выше или создай короткую понятную категорию на русском языке.
5. Сделай короткое описание (например, "Кофе и круассан", "Зарплата за июль").
6. Если в тексте упоминается время (например "вчера", "позавчера"), определи date_offset_days (-1 для вчера, -2 для позавчера и т.д.).

Текст пользователя: "{text}"
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ParsedTransaction,
                    temperature=0.1
                )
            )
            data = json.loads(response.text)
            return ParsedTransaction(**data)
        except Exception as e:
            logger.error(f"Error parsing text transaction with Gemini: {e}")
            raise e

    async def parse_receipt_photo(self, image_path: str, user_comment: str = "") -> ParsedTransaction:
        """Parses photo of a store receipt into structured financial transaction."""
        prompt = f"""
Ты — финансовый ассистент по распознаванию чеков и квитанций.
Внимательно распознай сумму и содержимое чека на фотографии.

Существующие категории: {', '.join(DEFAULT_CATEGORIES)}.
Правила:
1. Найди ИТОГОВУЮ сумму чека (Итог, К оплате, Total).
2. Валюта: По умолчанию UZS (сумы), если не указаны явно $ или USD.
3. Определи тип (обычно 'expense', если это чек покупки).
4. Определи категорию на основе перечня купленных товаров.
5. Напиши короткое описание чека.
6. Если пользователь добавил комментарий: "{user_comment}", учти его.

Верни результат в формате JSON.
"""
        image = Image.open(image_path)
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ParsedTransaction,
                    temperature=0.1
                )
            )
            data = json.loads(response.text)
            return ParsedTransaction(**data)
        except Exception as e:
            logger.error(f"Error parsing receipt photo with Gemini: {e}")
            raise e
