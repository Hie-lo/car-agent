from app.domain.enums import Currency, PriceMode


def rial_to_toman(amount_in_rials: int) -> int:
    """Converts Iranian Rials to integer Tomans (1 Toman = 10 Rials)."""
    raise NotImplementedError


def parse_persian_price(raw_text: str) -> tuple[int | None, PriceMode]:
    """
    Parses Persian raw price text into (amount_in_tomans, price_mode).
    Handles words like میلیارد, میلیون, تومان, ریال, توافقی.
    Returns (None, PriceMode.UNKNOWN) or (None, PriceMode.NEGOTIABLE) when appropriate.
    Missing/unknown is never silently 0.
    """
    raise NotImplementedError
