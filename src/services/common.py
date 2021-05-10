import requests
from bs4 import BeautifulSoup
from dateutil import tz
from ..logger import logging


logger = logging.getLogger(__name__)


# Set soup for site
def set_soup(url, targetEncoding="latin-1"):
    try:
        res = requests.get(url)
        if (res.status_code == 200):
            text = res.text.encode(targetEncoding)
            return BeautifulSoup(text, "html.parser")
        res.raise_for_status()
    except Exception:
        logger.exception(f"Error setting soup with url: {url}")


# Convert date between timezones
def convert_timezone(date, sourceTz=None, targetTz=None):
    if (sourceTz is None):
        sourceTz = tz.tzutc()
    else:
        sourceTz = tz.gettz(sourceTz)
    if (targetTz is None):
        targetTz = tz.tzutc()
    else:
        targetTz = tz.gettz(targetTz)
    date = date.replace(tzinfo=sourceTz)
    return date.astimezone(targetTz)
