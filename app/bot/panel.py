import logging
from telegram import Bot, InlineKeyboardMarkup, Message
from telegram.error import BadRequest

logger = logging.getLogger(__name__)


async def safe_edit_or_send_panel(
    bot: Bot,
    chat_id: int,
    message_id: int | None,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> Message:
    """
    Safely edits the existing panel message through user navigation steps.
    Gracefully handles 'Message is not modified' and missing messages,
    falling back to sending a new message when editing is impossible.
    Adheres to Section 12 of AGENTS.md.
    """
    if message_id:
        try:
            return await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
        except BadRequest as e:
            error_str = str(e).lower()
            if "message is not modified" in error_str:
                # No change in content, safe no-op
                return None
            logger.warning("Edit message %s in chat %s failed (%s), falling back to send_message", message_id, chat_id, e)

    # Fallback to sending a new panel message
    return await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
