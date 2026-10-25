from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Returns main navigation inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🔍 ثبت پایش خودرو جدید", callback_data="panel:new_watch"),
        ],
        [
            InlineKeyboardButton("📋 پایش‌های فعال من", callback_data="panel:my_watches"),
            InlineKeyboardButton("💳 طرح و اعتبار", callback_data="panel:credits"),
        ],
        [
            InlineKeyboardButton("❓ راهنمای استفاده", callback_data="panel:help"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Returns a simple back-to-menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="panel:main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def listing_notification_keyboard(direct_url: str, watch_id: str) -> InlineKeyboardMarkup:
    """Returns actionable buttons attached to a vehicle match notification."""
    keyboard = [
        [
            InlineKeyboardButton("🔗 مشاهده مستقیم در منبع", url=direct_url),
        ],
        [
            InlineKeyboardButton("🔕 توقف موقت این پایش", callback_data=f"watch:pause:{watch_id}"),
            InlineKeyboardButton("⚙️ پایش‌های من", callback_data="panel:my_watches"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def watch_actions_keyboard(watch_id: str, is_active: bool) -> InlineKeyboardMarkup:
    """Action buttons for a single watch."""
    toggle_text = "⏸️ توقف پایش" if is_active else "▶️ فعال‌سازی مجدد"
    toggle_data = f"watch:pause:{watch_id}" if is_active else f"watch:resume:{watch_id}"

    keyboard = [
        [
            InlineKeyboardButton(toggle_text, callback_data=toggle_data),
            InlineKeyboardButton("🗑️ حذف پایش", callback_data=f"watch:delete:{watch_id}"),
        ],
        [InlineKeyboardButton("🔙 بازگشت به پایش‌ها", callback_data="panel:my_watches")],
    ]
    return InlineKeyboardMarkup(keyboard)
