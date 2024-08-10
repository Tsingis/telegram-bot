import os
import telegram
from .common.logger import logging


logger = logging.getLogger(__name__)


class Bot:
    TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

    def __init__(self):
        self.tg_bot = telegram.Bot(self.TELEGRAM_TOKEN)
        self.chat_id = None

    async def send_text(self, text):
        try:
            await self.tg_bot.sendMessage(
                chat_id=self.chat_id,
                text=text,
                parse_mode="MarkdownV2",
                disable_web_page_preview=True,
            )
            logger.info("Text sent successfully")
        except Exception:
            logger.exception("Error sending text")

    async def send_image(self, image, caption=""):
        try:
            await self.tg_bot.sendPhoto(
                chat_id=self.chat_id,
                photo=image,
                caption=caption,
                parse_mode="MarkdownV2",
            )
            logger.info("Image sent successfully")
        except Exception:
            logger.exception("Error sending image")

    def get_message_text(self, data):
        try:
            update = telegram.Update.de_json(data, self.tg_bot)
            message = update.message
            self.chat_id = message.chat.id
            return message.text
        except Exception:
            logger.exception("Error getting bot message")

    async def set_webhook(self, url):
        return await self.tg_bot.set_webhook(url)
