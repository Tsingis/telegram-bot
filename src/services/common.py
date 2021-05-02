import requests
from bs4 import BeautifulSoup
import datetime as dt
import re
from ..logger import logging


logger = logging.getLogger(__name__)


# Set soup
def set_soup(url, target_encoding="latin-1"):
    try:
        res = requests.get(url)
        encoding = res.encoding
        text = res.content.decode(encoding).encode(target_encoding)
        return BeautifulSoup(text, "html.parser")
    except Exception:
        logger.exception(f"Error setting soup for url: {url}")


# Gets hour difference between UTC and local timezone
def get_timezone_difference(date=dt.datetime.utcnow()):
    if (dt.datetime(2020, 3, 29, 3) < date < dt.datetime(2020, 10, 25, 4)
            or dt.datetime(2021, 3, 28, 3) < date < dt.datetime(2021, 10, 31, 4)):
        hours = 3
    else:
        hours = 2
    return hours


# Time conversion from given time to local time
def convert_time_to_localtime(time, offset):
    time = dt.datetime.strptime(time, "%H:%M")

    # Add or subtract hours based on offset
    if offset[0] == "+":
        time = time - dt.timedelta(hours=int(offset[1:].split(":")[0]))
    else:
        time = time + dt.timedelta(hours=int(offset[1:].split(":")[0]))

    # Time difference between timezones
    hours = get_timezone_difference()

    # Convert datetime to HH:MM format
    return (time + dt.timedelta(hours=hours)).strftime("%H:%M")


# Replace special Markdown characters used in Telegram
def format_markdown(text):
    specials = ["*", "_"]
    return re.sub(rf"""(?<!\\)((?:\\\\)*)([{"".join(specials)}])""", r"\1\\\2", text)


# Removes linebreaks and whitespaces from text
def remove_linebreak_and_whitespace(text):
    return text.replace(" ", "").replace("\n", "")
