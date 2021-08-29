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
    if event["httpMethod"] == "POST" and event["body"]:
        logger.info("Message received")
        bot = set_bot()
        update = telegram.Update.de_json(json.loads(event["body"]), bot)
        chatId = update.message.chat.id
        msg = Message(bot, chatId)
        text = update.message.text
        if text and text.startswith("/"):
            cmd = Command(text)
            res = cmd.response()
            if res is not None:
                logger.info(f"Command received: {text}")
                if res.type == ResponseType.TEXT:
                    msg.send_text(res.text)
                if res.type == ResponseType.IMAGE:
                    msg.send_image(res.image)
                if res.type == ResponseType.TEXT_AND_IMAGE:
                    msg.send_image(res.image, res.text)
        return OK_RESPONSE
    return ERROR_RESPONSE


# Set webhook
def set_webhook(event, context):
    logger.info(f"Event: {event}")
    url = f"""https://{event["headers"]["Host"]}/{event["requestContext"]["stage"]}/"""
    bot = set_bot()
    webhook = bot.set_webhook(url)

    if webhook:
        return OK_RESPONSE

    return ERROR_RESPONSE


# Configure bot
def set_bot():
    telegram_token = os.environ["TELEGRAM_TOKEN"]
    return telegram.Bot(telegram_token)
