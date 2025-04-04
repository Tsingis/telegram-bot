import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
from http import HTTPStatus


def get(url, params=None):
    with requests.Session() as session:
        res = session.get(url, params=params)
        if res.status_code == HTTPStatus.OK:
            return res
        res.raise_for_status()


def set_soup(url, target_encoding="latin-1"):
    res = get(url)
    text = res.text.encode(target_encoding)
    return BeautifulSoup(text, "html.parser")


def find_first_integer(strings):
    for string in strings:
        if string.strip().replace("-", "").isdigit():
            return int(string)


def find_first_word(strings):
    for string in strings:
        if string.strip().isalpha():
            return string


def convert_timezone(dt, source_tz=None, target_tz=None):
    source_tz = source_tz if source_tz is not None else "UTC"
    target_tz = target_tz if target_tz is not None else "UTC"
    return dt.replace(tzinfo=ZoneInfo(source_tz)).astimezone(ZoneInfo(target_tz))


def text_to_datetime(text, pattern):
    return datetime.strptime(text, pattern)


def datetime_to_text(dt, pattern, source_tz=None, target_tz=None):
    result = convert_timezone(dt=dt, source_tz=source_tz, target_tz=target_tz)
    return datetime.strftime(result, pattern)


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


def format_as_monospace(text):
    return f"`{text}`"
