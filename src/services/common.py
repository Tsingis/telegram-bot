import requests
from bs4 import BeautifulSoup
from dateutil import tz
from ..logger import logging


logger = logging.getLogger(__name__)


# Set soup for site
def set_soup(url, target_encoding="latin-1"):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            text = res.text.encode(target_encoding)
            return BeautifulSoup(text, "html.parser")
        res.raise_for_status()
    except Exception:
        logger.exception(f"Error setting soup with url: {url}")


# Convert date between timezones
def convert_timezone(date, source_tz=None, target_tz=None):
    if source_tz is None:
        source_tz = tz.tzutc()
    else:
        source_tz = tz.gettz(source_tz)
    if target_tz is None:
        target_tz = tz.tzutc()
    else:
        target_tz = tz.gettz(target_tz)
    date = date.replace(tzinfo=source_tz)
    return date.astimezone(target_tz)
