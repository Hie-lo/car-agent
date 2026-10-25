from unittest.mock import AsyncMock, MagicMock
import pytest
from telegram.error import BadRequest, Forbidden
from app.bot.messages import (
    escape_user_content,
    format_listing_notification,
    format_toman_price,
)
from app.bot.panel import safe_edit_or_send_panel
from app.domain.enums import PriceMode
from app.workers.notifier import deliver_match_notification


class TestBotMessagesAndSafety:
    def test_seller_content_html_escaping(self):
        malicious = "<script>alert('xss')</script> & <b>bold</b>"
        escaped = escape_user_content(malicious)
        assert "<script>" not in escaped
        assert "&lt;script&gt;" in escaped
        assert "<b>" not in escaped
        assert "&lt;b&gt;" in escaped

    def test_format_toman_price_modes(self):
        assert format_toman_price(1_500_000_000, PriceMode.FIXED) == "1,500,000,000 تومان"
        assert format_toman_price(None, PriceMode.NEGOTIABLE) == "توافقی"
        assert format_toman_price(None, PriceMode.UNKNOWN) == "تماس بگیرید / نامشخص"

    def test_format_listing_notification_structure(self):
        msg = format_listing_notification(
            title="پژو 207 اتوماتیک سفید <مدل 1401>",
            make="پژو",
            model="207",
            year=1401,
            mileage=25000,
            city="تهران",
            price_toman=1_650_000_000,
            price_mode=PriceMode.FIXED,
            body_condition="بدون رنگ",
            engine_condition="سالم",
            match_score=85.0,
            data_confidence=100.0,
            reasons=["قیمت در محدوده بودجه است", "گیربکس اتوماتیک مطابق سلیقه"],
            source_name="دیوار",
            direct_url="https://divar.ir/v/abc1234",
        )
        assert "1,650,000,000 تومان" in msg
        assert "امتیاز تطابق:</b> 85/100" in msg
        assert "25,000 کیلومتر" in msg
        assert "&lt;مدل 1401&gt;" in msg  # safely escaped
        assert "https://divar.ir/v/abc1234" in msg


class TestPanelNavigationAndNotifier:
    @pytest.mark.asyncio
    async def test_safe_edit_normal(self):
        mock_bot = AsyncMock()
        mock_bot.edit_message_text.return_value = MagicMock(message_id=42)

        res = await safe_edit_or_send_panel(
            bot=mock_bot,
            chat_id=1001,
            message_id=42,
            text="صفحه جدید",
        )
        assert res.message_id == 42
        mock_bot.edit_message_text.assert_called_once()
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_safe_edit_message_not_modified_ignored(self):
        mock_bot = AsyncMock()
        mock_bot.edit_message_text.side_effect = BadRequest("Message is not modified: specified new message content")

        res = await safe_edit_or_send_panel(
            bot=mock_bot,
            chat_id=1001,
            message_id=42,
            text="صفحه تکراری",
        )
        assert res is None  # graceful no-op
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_safe_edit_fallback_to_send_message(self):
        mock_bot = AsyncMock()
        mock_bot.edit_message_text.side_effect = BadRequest("Message to edit not found")
        mock_bot.send_message.return_value = MagicMock(message_id=99)

        res = await safe_edit_or_send_panel(
            bot=mock_bot,
            chat_id=1001,
            message_id=42,
            text="صفحه جدید",
        )
        assert res.message_id == 99
        mock_bot.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_deliver_match_notification_success(self):
        mock_bot = AsyncMock()
        payload = {
            "title": "دنا پلاس",
            "make": "ایران خودرو",
            "model": "دنا پلاس",
            "price_toman": 950_000_000,
            "url": "https://divar.ir/v/test",
            "watch_id": "watch_123",
        }
        success = await deliver_match_notification(mock_bot, chat_id=1001, payload=payload)
        assert success is True
        mock_bot.send_message.assert_called_once()
        args, kwargs = mock_bot.send_message.call_args
        assert kwargs["chat_id"] == 1001
        assert "950,000,000 تومان" in kwargs["text"]

    @pytest.mark.asyncio
    async def test_deliver_match_notification_user_blocked(self):
        mock_bot = AsyncMock()
        mock_bot.send_message.side_effect = Forbidden("Forbidden: bot was blocked by the user")

        payload = {"title": "تارا", "url": "https://divar.ir/v/1"}
        success = await deliver_match_notification(mock_bot, chat_id=1001, payload=payload)
        assert success is False
