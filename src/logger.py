import logging
import json


logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)

logFormat = "%(asctime)s %(name)s %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=logFormat)

OK_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps("Ok!"),
}
ERROR_RESPONSE = {"statusCode": 400, "body": json.dumps("Something went wrong!")}
