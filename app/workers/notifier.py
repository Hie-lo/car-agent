import logging
from typing import Any
from telegram import Bot
from telegram.error import Forbidden, TelegramError
from app.bot.keyboards import listing_notification_keyboard
from app.bot.messages import format_listing_notification
from app.domain.enums import PriceMode

logger = logging.getLogger(__name__)


async def deliver_match_notification(
    bot: Bot,
    chat_id: int,
    payload: dict[str, Any],
) -> bool:
    """
    Delivers a matched listing notification message to the user on Telegram:
    - Formats concise, explainable HTML details
    - Attaches direct listing link and mute button
    - Handles user blocked bot or delivery errors gracefully
    """
    text = format_listing_notification(
        title=payload.get("title", "خودرو پیشنهادی جدید"),
        make=payload.get("make"),
        model=payload.get("model"),
        year=payload.get("year"),
        mileage=payload.get("mileage"),
        city=payload.get("city"),
        price_toman=payload.get("price_toman"),
        price_mode=PriceMode(payload.get("price_mode", "fixed")),
        body_condition=payload.get("body_condition"),
        engine_condition=payload.get("engine_condition"),
        match_score=float(payload.get("match_score", 70.0)),
        data_confidence=float(payload.get("data_confidence", 80.0)),
        reasons=payload.get("reasons", []),
        source_name=payload.get("source_name", "دیوار"),
        direct_url=payload.get("url", "https://divar.ir"),
    )

    markup = listing_notification_keyboard(
        direct_url=payload.get("url", "https://divar.ir"),
        watch_id=str(payload.get("watch_id", "")),
    )

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=markup,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )
        return True
    except Forbidden:
        logger.warning("User %s blocked the bot. Skipping notification.", chat_id)
        return False
    except TelegramError as e:
        logger.error("Failed to send notification to %s: %s", chat_id, e)
        raise
