import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import tz


def get(url, params=None):
    if params:
        res = requests.get(url, params)
    else:
        res = requests.get(url)
    if res.status_code == 200:
        return res
    res.raise_for_status()


def set_soup(url, target_encoding="latin-1"):
    res = get(url)
    text = res.text.encode(target_encoding)
    return BeautifulSoup(text, "html.parser")


def find_first_int(strings):
    for string in strings:
        if string.strip().isdigit():
            return int(string)


def find_first_word(strings):
    for string in strings:
        if string.strip().isalpha():
            return string


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


def text_to_datetime(text, pattern):
    return datetime.strptime(text, pattern)


def datetime_to_text(date, pattern, source_tz=None, target_tz=None):
    date = convert_timezone(date=date, source_tz=source_tz, target_tz=target_tz)
    return datetime.strftime(date, pattern)


def remove_texts(text, texts_to_remove):
    if not isinstance(texts_to_remove, list):
        texts_to_remove = [texts_to_remove]
    for text_to_remove in texts_to_remove:
        text = text.replace(text_to_remove, "")
    return text.strip()


def escape_special_chars(text):
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


def format_number(number):
    return f"{number:g}"


def format_as_url(url, text="Details"):
    return f"[{text}]({url})"


def format_as_header(text):
    return f"*{text}*"


def format_as_code(text):
    return f"```\n{text}\n```"
