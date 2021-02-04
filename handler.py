import telegram
import os
import json
from src.logger import logging, OK_RESPONSE, ERROR_RESPONSE
from src.command import Command, ResponseType
from src.message import Message


logger = logging.getLogger(__name__)


# Run webhook
def webhook(event, context):
    logger.info(f"Event: {event}")
    bot = set_bot()
    if event.get("httpMethod") == "POST" and event.get("body"):
        logger.info("Message received")
        update = telegram.Update.de_json(json.loads(event.get("body")), bot)
        chatId = update.message.chat.id
        msg = Message(bot, chatId)
        text = update.message.text
        if text and text.startswith("/"):
            logger.info("Command received")
            cmd = Command(text)
            res = cmd.response()
            if (res.type == ResponseType.TEXT):
                msg.send_text(res.text)
            if (res.type == ResponseType.IMAGE):
                msg.send_image(res.image)
            else:
                msg.send_image(res.image, res.text)
        return OK_RESPONSE
    return ERROR_RESPONSE


# Set webhook
def set_webhook(event, context):
    logger.info(f"Event: {event}")
    bot = set_bot()
    url = f"""https://{event.get("headers").get("Host")}/{event.get("requestContext").get("stage")}/"""
    webhook = bot.set_webhook(url)

    if webhook:
        return OK_RESPONSE

    return ERROR_RESPONSE


# Configure bot
def set_bot():
    telegram_token = os.environ["TELEGRAM_TOKEN"]
    return telegram.Bot(telegram_token)
