import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import tz
import re
from ..logger import logging


logger = logging.getLogger(__name__)


# Set soup for site
def set_soup(url, target_encoding="latin-1"):
    try:
        res = requests.get(url)
        encoding = res.encoding
        text = res.content.decode(encoding).encode(target_encoding)
        return BeautifulSoup(text, "html.parser")
    except Exception:
        logger.exception(f"Error setting soup for url: {url}")


# Change UTC to Finnish timezone
def convert_utc_to_local(date):
    timezone = tz.gettz("Europe/Helsinki")
    date = date.replace(tzinfo=tz.tzutc())
    return date.astimezone(timezone)


# Formats date with given input and output patterns
def format_date(date, pattern):
    date = convert_utc_to_local(date)
    return datetime.strftime(date, pattern)


# Replace special Markdown characters used in Telegram
def format_markdown(text):
    specials = ["*", "_"]
    return re.sub(rf"""(?<!\\)((?:\\\\)*)([{"".join(specials)}])""", r"\1\\\2", text)
