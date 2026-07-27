import aiohttp
import logging

logger = logging.getLogger(__name__)

# Default fallback rate if API fails: 1 USD = 12,850 UZS
DEFAULT_USD_RATE = 12850.0

cached_usd_rate: float = DEFAULT_USD_RATE


async def get_usd_uzs_rate() -> float:
    """Fetches official USD to UZS rate from Central Bank of Uzbekistan (CBU)."""
    global cached_usd_rate
    url = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for item in data:
                        if item.get("Ccy") == "USD":
                            rate = float(item.get("Rate", DEFAULT_USD_RATE))
                            cached_usd_rate = rate
                            logger.info(f"Fetched live USD/UZS rate from CBU: 1 USD = {rate} UZS")
                            return rate
    except Exception as e:
        logger.warning(f"Could not fetch CBU exchange rate, using cached/default {cached_usd_rate}: {e}")
    
    return cached_usd_rate


def convert_uzs_to_usd(amount_uzs: float, rate: float) -> float:
    """Converts UZS amount to USD."""
    if rate <= 0:
        return 0.0
    return amount_uzs / rate


def convert_usd_to_uzs(amount_usd: float, rate: float) -> float:
    """Converts USD amount to UZS."""
    return amount_usd * rate
