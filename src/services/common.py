import requests
import unicodedata
from datetime import datetime
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
        res = requests.get(url)
        if res.status_code == 200:
            text = res.text.encode(target_encoding)
            return BeautifulSoup(text, "html.parser")
        res.raise_for_status()
    except Exception:
        logger.exception(f"Error setting soup with url: {url}")


def format_date(date, pattern, target_tz="Europe/Helsinki"):
    """
    Formats date with specific output pattern and timezone
    """
    date = convert_timezone(date=date, target_tz=target_tz)
    return datetime.strftime(date, pattern)


def format_number(number):
    """
    Formats floating number without insignificant trailing zeroes
    """
    return f"{number:g}"


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


def normalize_text_encoding(text):
    """Normalizes text encoding"""
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("utf-8")
