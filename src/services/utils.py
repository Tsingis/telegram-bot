import re
import requests
from bs4 import BeautifulSoup
from dateutil import tz
from ..logger import logging


logger = logging.getLogger(__name__)


def get(url, params={}):
    """
    HTTP GET request with or without parameters
    """
    try:
        if params:
            res = requests.get(url, params)
        else:
            res = requests.get(url)
        if res.status_code == 200:
            return res
        res.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.exception(f"Error getting data with url: {url}")


def set_soup(url, target_encoding="latin-1"):
    """
    Set soup for given url
    """
    try:
        res = get(url)
        text = res.text.encode(target_encoding)
        return BeautifulSoup(text, "html.parser")
    except Exception:
        logger.exception(f"Error setting soup with url: {url}")


def convert_timezone(date, source_tz=None, target_tz=None):
    """
    Convert date between timezones
    """
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


def escape_special_chars(text):
    """
    Escapes MarkdownV2 engine special characters
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


def format_as_url(url, text="Details"):
    return f"[{text}]({url})"


def format_as_header(text):
    return f"*{text}*"


def format_as_code(text):
    return f"```\n{text}\n```"