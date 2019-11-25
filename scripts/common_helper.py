import urllib.request as request
from bs4 import BeautifulSoup
import datetime as dt
import re


# Set soup helper
def set_soup(url):
    content = request.urlopen(url).read()
    return BeautifulSoup(content, "html.parser")


# Gets hour difference between UTC and local timezone
def timezone_difference():
    datetime = dt.datetime.utcnow()
    if (dt.datetime(2020, 3, 29, 3) < datetime < dt.datetime(2020, 10, 25, 4)
        or dt.datetime(2021, 3, 28, 3) < datetime < dt.datetime(2019, 10, 31, 4)):
        hours = 3
    else:
        hours = 2
    return hours


# Replace special Markdown characters used in Telegram
def format_markdown(text):
    specials = ["*", "_"]
    return re.sub(rf"""(?<!\\)((?:\\\\)*)([{"".join(specials)}])""", r"\1\\\2", text)
