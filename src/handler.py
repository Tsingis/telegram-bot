import asyncio
import json
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
    logger.info(f"Event: {event}")
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
                    if res.type == ResponseType.IMAGE:
                        await bot.send_image(res.image)
                    if res.type == ResponseType.TEXT_AND_IMAGE:
                        await bot.send_image(res.image, res.text)
            logger.info("Event handled")
            return create_response(200, "Event handled")
        except Exception:
            logger.exception("Error handling event")
            return create_response(400, "Error handling event")
    logger.info("No event to handle")
    return create_response(400, "No event to handle")


async def set_webhook_async(event, context):
    logger.info(f"Event: {event}")
    try:
        url = f"""https://{event["headers"]["host"]}"""
        bot = Bot()
        webhook = await bot.set_webhook(url)
        if webhook:
            logger.info("Webhook set")
            return create_response(200, "Webhook set")
    except Exception:
        logger.exception("Error setting webhook")
        return create_response(400, "Error setting webhook")


def create_response(status_code, message):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(message),
    }
