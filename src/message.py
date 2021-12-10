from .logger import logging
from .services.utils import add_timestamp_to_image


logger = logging.getLogger(__name__)


class Message:
    def __init__(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id

    def send_text(self, text):
        try:
            self.bot.sendMessage(
                chat_id=self.chat_id,
                text=text,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True,
            )
            logger.info("Text sent successfully")
        except Exception:
            logger.exception("Error sending text")

    def send_image(self, image, caption=""):
        try:
            self.bot.sendPhoto(
                chat_id=self.chat_id,
                photo=add_timestamp_to_image(image),
                caption=caption,
                parse_mode="MarkdownV2",
            )
            logger.info("Image sent successfully")
        except Exception:
            logger.exception("Error sending image")
