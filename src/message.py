from .logger import logging


logger = logging.getLogger(__name__)


class Message:
    def __init__(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id

    async def send_text(self, text):
        try:
            await self.bot.sendMessage(
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
            await self.bot.sendPhoto(
                chat_id=self.chat_id,
                photo=image,
                caption=caption,
                parse_mode="MarkdownV2",
            )
            logger.info("Image sent successfully")
        except Exception:
            logger.exception("Error sending image")
