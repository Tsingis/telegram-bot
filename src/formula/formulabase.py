import os
from datetime import datetime


class FormulaBase:
    CALENDAR_URL = os.getenv("F1_CALENDAR_URL")

    def __init__(self, date=datetime.now()):
        self.base_url = "https://www.formula1.com"
        self.calendar = self.CALENDAR_URL
        self.date = date
        self.source_timezone = "Etc/UTC"
        self.source_datetime_pattern = "%Y%m%dT%H%M%S"
        self.target_date_pattern = "%b %d"
        self.target_day_and_time_pattern = "%a %H:%M"
        self.target_timezone = "Europe/Helsinki"
