import telegram
import os
import json
from src.logger import logging
from src.command import Command, ResponseType
from src.message import Message


logger = logging.getLogger(__name__)


def webhook(event, context):
    logger.info(f"Event: {event}")
    if event["httpMethod"] == "POST" and event["body"]:
        try:
            logger.info("Message received")
            bot = set_bot()
            update = telegram.Update.de_json(json.loads(event["body"]), bot)
            chat_id = update.message.chat.id
            msg = Message(bot, chat_id)
            text = update.message.text
            if text and text.startswith("/"):
                cmd = Command(text)
                res = cmd.response
                if res is not None:
                    logger.info(f"Command received: {text}")
                    if res.type == ResponseType.TEXT:
                        msg.send_text(res.text)
                    if res.type == ResponseType.IMAGE:
                        msg.send_image(res.image)
                    if res.type == ResponseType.TEXT_AND_IMAGE:
                        msg.send_image(res.image, res.text)
            return create_response(200, "Event handled")
        except Exception:
            logger.exception("Error handling event")
            return create_response(400, "Error handling event")
    return create_response(400, "No event to handle")


def set_webhook(event, context):
    logger.info(f"Event: {event}")
    url = f"""https://{event["headers"]["Host"]}/{event["requestContext"]["stage"]}/"""
    bot = set_bot()
    webhook = bot.set_webhook(url)
    if webhook:
        logger.info("Webhook set")
        return create_response(200, "Webhook set")

    logger.error("Error setting webhook")
    return create_response(400, "Error setting webhook")


def set_bot():
    telegram_token = os.environ["TELEGRAM_TOKEN"]
    return telegram.Bot(telegram_token)


def create_response(status_code, message):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(message),
    }
