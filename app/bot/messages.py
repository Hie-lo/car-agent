import html
from typing import Any
from app.domain.enums import PriceMode


def escape_user_content(text: str | None) -> str:
    """Escapes seller/user input to prevent Telegram HTML entity injection."""
    if not text:
        return ""
    return html.escape(str(text))


def format_toman_price(price: int | None, mode: PriceMode) -> str:
    """Formats price in integer tomans or descriptive mode."""
    if mode == PriceMode.NEGOTIABLE:
        return "توافقی"
    if price is None or mode == PriceMode.UNKNOWN:
        return "تماس بگیرید / نامشخص"
    return f"{price:,} تومان"


def format_listing_notification(
    title: str,
    make: str | None,
    model: str | None,
    year: int | None,
    mileage: int | None,
    city: str | None,
    price_toman: int | None,
    price_mode: PriceMode,
    body_condition: str | None,
    engine_condition: str | None,
    match_score: float,
    data_confidence: float,
    reasons: list[str],
    source_name: str,
    direct_url: str,
) -> str:
    """
    Constructs a concise, structured Telegram HTML notification for a matched listing.
    Adheres to Section 12 of AGENTS.md.
    """
    safe_title = escape_user_content(title)
    safe_make = escape_user_content(make or "نامشخص")
    safe_model = escape_user_content(model or "")
    safe_city = escape_user_content(city or "نامشخص")
    safe_body = escape_user_content(body_condition or "اظهار نشده توسط فروشنده")
    safe_engine = escape_user_content(engine_condition or "اظهار نشده")
    safe_url = escape_user_content(direct_url)
    safe_source = escape_user_content(source_name)

    formatted_price = format_toman_price(price_toman, price_mode)
    mileage_str = f"{mileage:,} کیلومتر" if mileage is not None else "نامشخص"
    year_str = str(year) if year is not None else "نامشخص"

    reasons_bullet = "\n".join(f"• {escape_user_content(r)}" for r in reasons) if reasons else "• تطابق با فیلترهای اولیه"

    confidence_note = ""
    if data_confidence < 90:
        confidence_note = f"\n⚠️ <i>اطمینان داده: {int(data_confidence)}% (برخی مشخصات فنی توسط فروشنده اظهار نشده است)</i>"

    return (
        f"🚗 <b>{safe_title}</b>\n\n"
        f"▫️ <b>خودرو:</b> {safe_make} {safe_model}\n"
        f"▫️ <b>قیمت:</b> {formatted_price}\n"
        f"▫️ <b>سال ساخت:</b> {year_str}\n"
        f"▫️ <b>کارکرد:</b> {mileage_str}\n"
        f"▫️ <b>شهر:</b> {safe_city}\n"
        f"▫️ <b>وضعیت بدنه:</b> {safe_body}\n"
        f"▫️ <b>وضعیت موتور:</b> {safe_engine}\n\n"
        f"🎯 <b>امتیاز تطابق:</b> {int(match_score)}/100\n"
        f"📋 <b>علت پیشنهاد:</b>\n{reasons_bullet}"
        f"{confidence_note}\n\n"
        f"منبع: {safe_source} | <a href=\"{safe_url}\">مشاهده آگهی اصلی</a>"
    )


def format_main_menu(telegram_user_name: str, credits_remaining: int, active_watches_count: int) -> str:
    """Main menu panel message."""
    safe_name = escape_user_content(telegram_user_name)
    return (
        f"سلام <b>{safe_name}</b> عزیز، به رادار خودرو خوش آمدید 🚘\n\n"
        f"📊 <b>وضعیت حساب شما:</b>\n"
        f"• اعتبار روزانه باقی‌مانده: <b>{credits_remaining}</b>\n"
        f"• پایش‌های فعال: <b>{active_watches_count}</b>\n\n"
        f"از منوی زیر می‌توانید پایش جدیدی ثبت کنید یا وضعیت پایش‌های خود را مدیریت نمایید:"
    )
