import pytest
from app.domain.enums import PriceMode
from app.domain.money import parse_persian_price, rial_to_toman
from app.services.normalization import normalize_digits, normalize_persian_text


class TestPersianNormalization:
    def test_normalize_arabic_letters_to_persian(self):
        # Arabic Yeh and Kaf to Persian
        text = "خودروی بي‌رنگ با كمك‌فنر سالم"
        normalized = normalize_persian_text(text)
        assert "ی" in normalized and "ي" not in normalized
        assert "ک" in normalized and "ك" not in normalized

    def test_normalize_persian_and_arabic_digits(self):
        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        arabic_digits = "٠١٢٣٤٥٦٧٨٩"
        assert normalize_digits(persian_digits) == "0123456789"
        assert normalize_digits(arabic_digits) == "0123456789"

    def test_normalize_whitespace_and_zwnj(self):
        text = "پژو    ۲۰۶   تیپ  ۲ "
        normalized = normalize_persian_text(text)
        assert "  " not in normalized
        assert normalized.strip() == "پژو 206 تیپ 2"


class TestMoneyConversionAndParsing:
    def test_rial_to_toman_conversion(self):
        # 1 Toman = 10 Rials
        assert rial_to_toman(15_000_000_000) == 1_500_000_000
        assert rial_to_toman(10) == 1
        assert rial_to_toman(0) == 0

    def test_parse_persian_price_billion_and_million(self):
        # 1.5 میلیارد تومان -> 1,500,000,000 Tomans
        price, mode = parse_persian_price("۱.۵ میلیارد تومان")
        assert price == 1_500_000_000
        assert mode == PriceMode.FIXED

        # 550 میلیون تومان -> 550,000,000 Tomans
        price, mode = parse_persian_price("۵۵۰ میلیون")
        assert price == 550_000_000
        assert mode == PriceMode.FIXED

    def test_parse_persian_price_negotiable_and_unknown(self):
        price, mode = parse_persian_price("توافقی")
        assert price is None
        assert mode == PriceMode.NEGOTIABLE

        price, mode = parse_persian_price("تماس بگیرید")
        assert price is None
        assert mode == PriceMode.UNKNOWN

    def test_unknown_price_is_not_silently_zero(self):
        price, mode = parse_persian_price("")
        assert price is None
        assert price != 0
        assert mode == PriceMode.UNKNOWN
