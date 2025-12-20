import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo
from icalendar import Calendar
from .formulabase import FormulaBase
from ..common.logger import logging
from ..common.utils import (
    format_as_monospace,
    format_as_header,
    format_as_url,
    get,
    datetime_to_text,
    remove_texts,
    set_selector,
    text_to_datetime,
)


logger = logging.getLogger(__name__)


class FormulaRace(FormulaBase):
    def __init__(self):
        super().__init__()

    def get_upcoming(self):
        """
        Gets info for the upcoming race
        """
        try:
            race_weekends = self._get_race_weekends()
            race = next(
                (race for race in race_weekends if race["sessions"]["race"] >= self.date),
                race_weekends[-1],
            )
            return race
        except Exception:
            logger.exception(f"Error getting upcoming race for year {self.date.year}")

    def format(self, data):
        header = "Upcoming race:"
        sessions = dict(sorted(data["sessions"].items(), key=lambda x: x[1]))
        sessions = {k[:12]: v for k, v in sessions.items()}
        first_date, last_date = min(sessions.values()), max(sessions.values())
        date_info = f"{datetime_to_text(first_date, self.target_date_pattern, target_tz=self.target_timezone)} to {datetime_to_text(last_date, self.target_date_pattern, target_tz=self.target_timezone)}"

        name = remove_texts(data["name"], ["FORMULA 1", str(self.date.year)])
        info = f"""{name}\n""" + f"""{data["location"]}\n""" + date_info

        for session, date in sessions.items():
            info += f"\n{datetime_to_text(date, self.target_day_and_time_pattern, target_tz=self.target_timezone)} - {session.title()}"

        text = (
            format_as_header(header)
            + "\n"
            + format_as_monospace(info)
            + "\n"
            + format_as_url(data["raceUrl"])
        )
        return text

    def find_circuit_image(self, url):
        """
        Gets image for race circuit
        """
        try:
            selector = set_selector(url, "utf8")
            img_urls = selector.xpath(
                "//img[contains(translate(@alt, 'PNG', 'png'), '.png')]/@src"
            ).getall()
            img_url = next(src for src in img_urls if "circuit" in src.lower())
            return self._add_timestamp_to_image(img_url)
        except Exception:
            logger.exception("Error getting circuit image")

    def _add_timestamp_to_image(self, img):
        if isinstance(img, str):
            return f"{img}?a={datetime.now().isoformat()}"
        return img

    def _get_race_weekends(self):
        try:
            res = get(self.calendar_url)
            calendar = Calendar.from_ical(res.content)
            events = [self._event_to_dict(event) for event in calendar.walk("VEVENT")]
            if not events:
                logger.info(f"No events available for year {self.date.year}")
                return
            race_weekends = self._events_to_race_weekends(events)
            if not race_weekends:
                logger.info(f"No race weekends available for year {self.date.year}")
                return
            return race_weekends
        except Exception:
            logger.exception(f"Error getting calendar data with url {self.calendar_url}")

    def _events_to_race_weekends(self, events):
        """
        Parse and combine scheduled events to race weekends
        """
        events = sorted(self._filter_events(events), key=lambda x: x["startTime"])
        race_weekends = []
        for event in events:
            if any(rw["name"] == event["name"] for rw in race_weekends):
                for rw in race_weekends:
                    if rw["name"] == event["name"]:
                        rw["sessions"][event["session"]] = self._format_date_utc(event["startTime"])
            else:
                race_weekend = {
                    "name": event["name"],
                    "raceUrl": self._find_race_url(event["description"]),
                    "location": event["location"],
                    "sessions": {event["session"]: self._format_date_utc(event["startTime"])},
                }
                race_weekends.append(race_weekend)

        for index, race_weekend in enumerate(race_weekends):
            race_weekend["round"] = index + 1
        return race_weekends

    def _event_to_dict(self, event):
        summary = self._normalize_text_encoding(event["SUMMARY"])
        start_time = event["DTSTART"].dt
        if not isinstance(start_time, datetime):
            start_time = datetime.combine(start_time, datetime.min.time(), tzinfo=ZoneInfo("UTC"))
        return {
            "startTime": start_time,
            "name": summary.split(" - ")[0].strip(),
            "session": summary.split(" - ")[-1].lower(),
            "description": str(event["DESCRIPTION"]).strip(),
            "location": str(event["LOCATION"]).strip(),
        }

    def _filter_events(self, events):
        allowed_words = [
            "race",
            "sprint race",
            "sprint qualification",
            "qualifying",
            "practice",
        ]
        unallowed_words = ["testing", "pre-season"]
        return [
            event
            for event in events
            if any(word in event["session"].lower() for word in allowed_words)
            and not any(word in event["session"].lower() for word in unallowed_words)
        ]

    def _find_race_url(self, text):
        pattern = "Race Hub\\n(.*?)\\n"
        return re.search(pattern, text).group(1)

    def _format_date_utc(self, date):
        datetime_adjusted = datetime_to_text(
            dt=date,
            pattern=self.source_datetime_pattern,
            source_tz=self.source_timezone,
        )
        return text_to_datetime(datetime_adjusted, self.source_datetime_pattern)

    def _normalize_text_encoding(self, text):
        normalized = unicodedata.normalize("NFKD", text)
        return normalized.encode("ascii", "ignore").decode("utf-8")
