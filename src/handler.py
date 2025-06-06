import asyncio
import json
from http import HTTPStatus
from .bot import Bot
from .command import Command, ResponseType
from .common.logger import logging


logger = logging.getLogger(__name__)


def webhook(event, context):
    result = asyncio.run(webhook_async(event, context))
    return result


def set_webhook(event, context):
    result = asyncio.run(set_webhook_async(event, context))
    return result


async def webhook_async(event, context):
    if event["requestContext"]["http"]["method"] == "POST" and event["body"]:
        try:
            logger.info("Message received")
            data = json.loads(event["body"])
            bot = Bot()
            text = bot.get_message_text(data)
            if text and text.startswith("/"):
                cmd = Command(text)
                res = cmd.response
                if res is not None:
                    logger.info(f"Command received: {text}")
                    if res.type == ResponseType.TEXT:
                        await bot.send_text(res.text)
                    else:
                        await bot.send_image(res.image, res.text)
            logger.info("Event handled")
            return create_response(HTTPStatus.OK, "Event handled")
        except Exception:
            logger.exception("Error handling event")
            return create_response(HTTPStatus.INTERNAL_SERVER_ERROR, "Error handling event")
    logger.info("No event to handle")
    return create_response(HTTPStatus.OK, "No event to handle")


async def set_webhook_async(event, context):
    try:
        url = f"""https://{event["headers"]["host"]}"""
        bot = Bot()
        webhook = await bot.set_webhook(url)
        if webhook:
            logger.info("Webhook set")
            return create_response(HTTPStatus.OK, "Webhook set")
    except Exception:
        logger.exception("Error setting webhook")
        return create_response(HTTPStatus.INTERNAL_SERVER_ERROR, "Error setting webhook")


def create_response(status_code, message):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(message),
    }
