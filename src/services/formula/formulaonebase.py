from datetime import datetime
from icalendar import Calendar
import unicodedata
from ..utils import get, datetime_to_text, text_to_datetime
from ...logger import logging


logger = logging.getLogger(__name__)


class FormulaOneBase:
    F1_CALENDAR_URL = "https://formula1.com/calendar/Formula_1_Official_Calendar.ics"

    def __init__(self, date=datetime.utcnow()):
        self.date = date
        self.source_timezone = "Europe/London"
        self.source_datetime_pattern = "%Y%m%dT%H%M%S"
        self.race_weekends = self._get_race_weekends()
        self.races_amount = 0 if self.race_weekends is None else len(self.race_weekends)

    def _get_race_weekends(self):
        try:
            res = get(self.F1_CALENDAR_URL)
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
            logger.exception(
                f"Error getting calendar data with url {self.F1_CALENDAR_URL}"
            )

    def _events_to_race_weekends(self, events):
        """
        Parse and combine scheduled events to race weekends
        """
        events = sorted(
            self._filter_cancelled_events(events),
            key=lambda x: x["startTime"],
        )
        race_weekends = [
            {
                "id": event["id"],
                "type": event["type"],
                "name": event["summary"].split("-")[0].strip(),
                "raceUrl": self._find_race_url(event["description"]),
                "location": event["location"],
                "sessions": {"race": self._format_date_utc(event["startTime"])},
            }
            for event in events
            if event["type"] == "race"
        ]

        for event in events:
            for race_weekend in race_weekends:
                if (
                    race_weekend["id"] == event["id"]
                    and race_weekend["type"] != event["type"]
                ):
                    race_weekend["sessions"][event["type"]] = self._format_date_utc(
                        event["startTime"]
                    )
                    continue

        for index, race_weekend in enumerate(race_weekends):
            race_weekend["round"] = index + 1

        return race_weekends

    def _event_to_dict(self, event):
        uid = str(event["UID"])
        return {
            "id": uid.split("@")[-1].strip(),
            "status": str(event["STATUS"]).strip().lower(),
            "type": uid.split("@")[0].strip().lower(),
            "startTime": event["DTSTART"].dt,
            "endTime": event["DTEND"].dt,
            "summary": self._normalize_text_encoding(event["SUMMARY"]),
            "description": str(event["DESCRIPTION"]).strip(),
            "location": str(event["LOCATION"]).strip(),
        }

    def _filter_cancelled_events(self, events):
        return [event for event in events if event["status"] != "cancelled"]

    def _find_race_url(self, text):
        pattern = "https://www.formula1.com/en/racing"
        return next(
            (word for word in text.split(" ") if word.startswith(pattern)), pattern
        )

    def _format_date_utc(self, date):
        datetime_adjusted = datetime_to_text(
            date=date,
            pattern=self.source_datetime_pattern,
            source_tz=self.source_timezone,
        )
        return text_to_datetime(datetime_adjusted, self.source_datetime_pattern)

    def _normalize_text_encoding(self, text):
        normalized = unicodedata.normalize("NFKD", text)
        return normalized.encode("ascii", "ignore").decode("utf-8")
