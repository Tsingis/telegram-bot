from .logger import logging


logger = logging.getLogger(__name__)


class Message:
    def __init__(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id

    def send_text(self, text):
        try:
            self.bot.sendMessage(
                chat_id=self.chat_id,
                text=self._as_code(text),
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )
            logger.info("Text sent successfully")
        except Exception:
            logger.exception("Error sending text")

    def send_image(self, image, caption=""):
        try:
            self.bot.sendPhoto(
                chat_id=self.chat_id,
                photo=image,
                caption=self._as_code(caption),
                parse_mode="Markdown",
            )
            logger.info("Image sent successfully")
        except Exception:
            logger.exception("Error sending image")

    def _as_code(self, text):
        return f"```{text}```"
