from .logger import logger, OK_RESPONSE, ERROR_RESPONSE


class Message():
    def __init__(self, bot, chatId):
        self.bot = bot
        self.chatId = chatId

    def send_text(self, text):
        try:
            self.bot.sendMessage(chat_id=self.chatId, text=text, parse_mode="Markdown",
                                 disable_web_page_preview=True)
            logger.info("Message sent")
            return OK_RESPONSE
        except Exception:
            return ERROR_RESPONSE

    def send_image(self, image, text=""):
        try:
            self.bot.sendPhoto(chat_id=self.chatId, photo=image, caption=text, parse_mode="Markdown")
            logger.info("Photo sent")
            return OK_RESPONSE
        except Exception:
            return ERROR_RESPONSE
