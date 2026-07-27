import json
import logging
import re
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


def fallback_parse_text(text: str) -> Optional[ParsedTransaction]:
    """Local regex parser for text transactions without AI dependency."""
    text_lower = text.lower()
    
    # Currency
    if any(c in text_lower for c in ['$', 'usd', 'доллар', 'баксов', 'баксы']):
        currency = "USD"
    else:
        currency = "UZS"
        
    # Extract numbers (e.g. 40000, 40 000, 25.5)
    numbers = re.findall(r'\b\d[\d\s._]*\d\b|\b\d+\b', text)
    clean_nums = []
    for n in numbers:
        cleaned = n.replace(' ', '').replace('_', '')
        try:
            val = float(cleaned)
            clean_nums.append(val)
        except ValueError:
            pass
            
    if not clean_nums:
        return None
        
    # Amount: pick maximum number if multiple numbers (e.g. "2 штуки за 40000 сум" -> 40000)
    amount = max(clean_nums)
    
    # Type
    if any(w in text_lower for w in ['доход', 'зарплата', 'аванс', 'получил', 'перевод мне', 'пришли', 'заработал']):
        tx_type = "income"
        category = "Доходы"
    else:
        tx_type = "expense"
        if any(w in text_lower for w in ['арбуз', 'арбузы', 'хлеб', 'молоко', 'продукты', 'еда', 'мясо', 'сыр', 'масло', 'сахар', 'картошка', 'овощи', 'фрукты']):
            category = "Продукты"
        elif any(w in text_lower for w in ['кофе', 'чай', 'сок', 'вода', 'напитки', 'кола', 'пепси']):
            category = "Напитки"
        elif any(w in text_lower for w in ['ресторан', 'кафе', 'обед', 'ужин', 'пицца', 'суши', 'бургер', 'доставка', 'столовая']):
            category = "Кафе и рестораны"
        elif any(w in text_lower for w in ['такси', 'метро', 'автобус', 'бензин', 'транспорт', 'парковка', 'яндекс', 'проезд']):
            category = "Транспорт"
        elif any(w in text_lower for w in ['аптека', 'врач', 'лекарства', 'больница', 'здоровье', 'таблетки']):
            category = "Здоровье и аптека"
        elif any(w in text_lower for w in ['одежда', 'обувь', 'шопинг', 'куртка', 'штаны', 'футболка']):
            category = "Одежда и шопинг"
        elif any(w in text_lower for w in ['свет', 'газ', 'вода', 'жкх', 'аренда', 'квартплата', 'интернет', 'связь']):
            category = "Жилье и ЖКХ"
        else:
            category = "Разное"
            
    date_offset = 0
    if 'позавчера' in text_lower:
        date_offset = -2
    elif 'вчера' in text_lower:
        date_offset = -1
        
    return ParsedTransaction(
        type=tx_type,
        amount=amount,
        currency=currency,
        category=category,
        description=text[:100].strip().capitalize(),
        date_offset_days=date_offset
    )


class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or settings.GEMINI_API_KEY
        self.client = None
        if key:
            try:
                self.client = genai.Client(api_key=key)
            except Exception as e:
                logger.warning(f"Gemini client init skipped/failed: {e}")
        self.model_name = "gemini-2.5-flash"

    async def parse_text_transaction(self, text: str) -> ParsedTransaction:
        """Parses text message into structured financial transaction."""
        if self.client:
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
                logger.warning(f"Gemini API call failed, using local parser: {e}")

        # Local parser (works without any API key)
        parsed = fallback_parse_text(text)
        if parsed:
            return parsed
        raise ValueError("Could not parse transaction from text.")

    async def parse_receipt_photo(self, image_path: str, user_comment: str = "") -> ParsedTransaction:
        """Parses photo of a store receipt into structured financial transaction."""
        if self.client:
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
            try:
                image = Image.open(image_path)
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
                logger.warning(f"Gemini photo parsing failed, using fallback: {e}")

        if user_comment:
            parsed = fallback_parse_text(user_comment)
            if parsed:
                return parsed

        return ParsedTransaction(
            type="expense",
            amount=0.0,
            currency="UZS",
            category="Разное",
            description="Чек с фото",
            date_offset_days=0
        )
