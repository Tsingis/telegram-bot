import logging
import json


# TODO Better logging and utilizing CloudWatch

# Set up logging
logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

OK_RESPONSE = {
    "statusCode": 200,
    "headers": {"Content-Type": "application/json"},
    "body": json.dumps("ok")
}
ERROR_RESPONSE = {
    "statusCode": 400,
    "body": json.dumps("Something went wrong!")
}
