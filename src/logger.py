import logging
import json


# Set up logging
logger = logging.getLogger()
if (logger.handlers):
    for handler in logger.handlers:
        logger.removeHandler(handler)

format = "%(asctime)s %(name)s %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=format)

OK_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps("ok")
}
ERROR_RESPONSE = {
    "statusCode": 400,
    "body": json.dumps("Something went wrong!")
}
