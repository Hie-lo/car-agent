import re

# Character translation tables for Arabic to Persian and Persian/Arabic digits to ASCII
_DIGIT_MAP = str.maketrans({
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
    "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
})

_CHAR_MAP = str.maketrans({
    "ي": "ی",
    "ى": "ی",
    "ك": "ک",
    "ۀ": "ه",
    "ة": "ه",
})


def normalize_digits(text: str) -> str:
    """Converts Persian (۰-۹) and Arabic (٠-٩) digits to ASCII digits (0-9)."""
    return text.translate(_DIGIT_MAP)


def normalize_persian_text(text: str) -> str:
    """
    Normalizes Persian text:
    - Replaces Arabic Yeh (ي, ى) with Persian Yeh (ی)
    - Replaces Arabic Kaf (ك) with Persian Kaf (ک)
    - Normalizes Heh variants (ۀ -> ه)
    - Normalizes Persian/Arabic digits to ASCII
    - Trims excess whitespace while preserving word boundaries
    """
    if not text:
        return ""
    text = text.translate(_CHAR_MAP)
    text = normalize_digits(text)
    # Collapse multiple spaces and ZWNJ cleanups
    text = re.sub(r"[\s\u200c]+", " ", text).strip()
    return text
