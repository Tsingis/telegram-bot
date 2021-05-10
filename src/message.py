from .logger import logging


logger = logging.getLogger(__name__)


class Message():
    def __init__(self, bot, chatId):
        self.bot = bot
        self.chatId = chatId

    def send_text(self, text):
        try:
            self.bot.sendMessage(chat_id=self.chatId, text=text, parse_mode="Markdown",
                                 disable_web_page_preview=True)
            logger.info("Text sent successfully")
        except Exception:
            logger.exception("Error sending text")

    def send_image(self, image, caption=""):
        try:
            self.bot.sendPhoto(chat_id=self.chatId, photo=image,
                               caption=caption, parse_mode="Markdown")
            logger.info("Image sent successfully")
        except Exception:
            logger.exception("Error sending image")
