def normalize_digits(text: str) -> str:
    """Converts Persian (۰-۹) and Arabic (٠-٩) digits to ASCII digits (0-9)."""
    raise NotImplementedError


def normalize_persian_text(text: str) -> str:
    """
    Normalizes Persian text:
    - Replaces Arabic Yeh (ي, ى) with Persian Yeh (ی)
    - Replaces Arabic Kaf (ك) with Persian Kaf (ک)
    - Normalizes Heh variants (ۀ -> ه)
    - Normalizes Persian/Arabic digits to ASCII
    - Normalizes zero-width non-joiner (ZWNJ / نیم‌فاصله) and trims excess whitespace/punctuation
    """
    raise NotImplementedError
