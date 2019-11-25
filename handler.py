import telegram
import os
import json

from logger import logger, OK_RESPONSE, ERROR_RESPONSE
from commands import command_response


# Configure bot
def set_bot():
    telegram_token = os.environ["TELEGRAM_TOKEN"]
    return telegram.Bot(telegram_token)


# Run webhook
def webhook(event, context):
    logger.info("Event: {}".format(event))
    bot = set_bot()

    if event.get("httpMethod") == "POST" and event.get("body"):
        logger.info("Message received")
        update = telegram.Update.de_json(json.loads(event.get("body")), bot)
        chat_id = update.message.chat.id
        text = update.message.text

        if text and text.startswith("/"):
            command_response(text, bot, chat_id)

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
