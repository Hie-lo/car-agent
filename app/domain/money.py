import re
from app.domain.enums import PriceMode
from app.services.normalization import normalize_digits, normalize_persian_text


def rial_to_toman(amount_in_rials: int) -> int:
    """Converts Iranian Rials to integer Tomans (1 Toman = 10 Rials)."""
    return amount_in_rials // 10


def parse_persian_price(raw_text: str) -> tuple[int | None, PriceMode]:
    """
    Parses Persian raw price text into (amount_in_tomans, price_mode).
    Standardizes on integer Tomans.
    Missing/unknown is returned as (None, PriceMode.UNKNOWN), never silently 0.
    """
    if not raw_text or not raw_text.strip():
        return None, PriceMode.UNKNOWN

    clean_text = normalize_persian_text(raw_text)

    if "توافقی" in clean_text:
        return None, PriceMode.NEGOTIABLE

    if any(keyword in clean_text for keyword in ("تماس", "نامشخص", "غیرفعال")):
        return None, PriceMode.UNKNOWN

    # Check for billion (میلیارد)
    billion_match = re.search(r"([\d\.]+)\s*میلیارد", clean_text)
    million_match = re.search(r"([\d\.]+)\s*میلیون", clean_text)

    if billion_match or million_match:
        total = 0.0
        if billion_match:
            total += float(billion_match.group(1)) * 1_000_000_000
        if million_match:
            total += float(million_match.group(1)) * 1_000_000
        return int(total), PriceMode.FIXED

    # Check for explicit Rial or standard integer digits
    digits_only = re.sub(r"[^\d]", "", clean_text)
    if not digits_only:
        return None, PriceMode.UNKNOWN

    amount = int(digits_only)
    if "ریال" in clean_text:
        amount = rial_to_toman(amount)

    return amount, PriceMode.FIXED
