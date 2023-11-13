from datetime import datetime


class FormulaBase:
    def __init__(self, date=datetime.utcnow()):
        self.base_url = "https://www.formula1.com"
        self.calendar_url = (
            "https://ics.ecal.com/ecal-sub/63ffa269e01772000d24b070/Formula%201.ics"
        )
        self.date = date
        self.source_timezone = "Etc/UTC"
        self.source_datetime_pattern = "%Y%m%dT%H%M%S"
        self.target_date_pattern = "%b %d"
        self.target_day_and_time_pattern = "%a %H:%M"
        self.target_timezone = "Europe/Helsinki"
