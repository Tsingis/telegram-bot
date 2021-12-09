from datetime import datetime
from icalendar import Calendar
import unicodedata
from ..utils import get, convert_timezone
from ...logger import logging


logger = logging.getLogger(__name__)


class FormulaOneBase:
    CALENDAR_URL = "http://www.formula1.com/calendar/Formula_1_Official_Calendar.ics"

    def __init__(self):
        self.source_timezone = "Europe/London"
        self.source_datetime_pattern = "%Y-%m-%dT%H:%M:%S.%f"
        self.race_weekends = self._get_race_weekends()
        self.races_amount = len(self.race_weekends)

    def _get_race_weekends(self):
        """
        Parse and combine scheduled qualifying and race events to race weekends
        """
        try:
            res = get(self.CALENDAR_URL)
            calendar = Calendar.from_ical(res.content)
            all_events = [
                self._event_to_dict(event) for event in calendar.walk("VEVENT")
            ]
            events = sorted(
                self._filter_cancelled_events(all_events),
                key=lambda x: x["startTime"],
            )
            qualifs = self._filter_events_by_type(events, ["qualifying"])
            races = self._filter_events_by_type(events, ["race"])
            race_weekends = self._events_to_race_weekends(qualifs, races)
            return race_weekends
        except Exception:
            logger.exception(f"Error getting data for url: {self.CALENDAR_URL}")

    def _event_to_dict(self, event):
        uid = str(event["UID"])
        return {
            "id": uid.split("@")[-1].strip(),
            "status": str(event["STATUS"]).strip(),
            "type": uid.split("@")[0].strip(),
            "startTime": event["DTSTART"].dt,
            "endTime": event["DTEND"].dt,
            "summary": self._normalize_text_encoding(event["SUMMARY"]),
            "description": str(event["DESCRIPTION"]).strip(),
            "location": str(event["LOCATION"]).strip(),
        }

    def _events_to_race_weekends(self, qualifs, races):
        race_weekends = []
        for index, race in enumerate(races):
            qualif = next(
                (qualif for qualif in qualifs if qualif["id"] == race["id"]), None
            )
            if qualif is None:
                raise Exception("No matching race and qualifying events")
            race_weekend = {
                "raceNumber": index + 1,
                "raceName": race["summary"].split("-")[0].strip(),
                "qualifyingTime": self._format_date_utc(qualif["startTime"]),
                "raceTime": self._format_date_utc(race["startTime"]),
                "raceUrl": self._find_race_url(race["description"]),
                "location": race["location"],
            }
            race_weekends.append(race_weekend)
        return race_weekends

    def _filter_cancelled_events(self, events):
        return [event for event in events if event["status"].lower() != "cancelled"]

    def _filter_events_by_type(self, events, types):
        return [
            event
            for event in events
            if any(keyword.lower() in event["type"].lower() for keyword in types)
        ]

    def _find_race_url(self, text):
        pattern = "https://www.formula1.com/en/racing"
        return next(
            (word for word in text.split(" ") if word.startswith(pattern)), pattern
        )

    def _format_date_utc(self, date):
        date_tz_adjust = convert_timezone(date=date, source_tz=self.source_timezone)
        date = date_tz_adjust.strftime(self.source_datetime_pattern)
        return datetime.strptime(date, self.source_datetime_pattern)

    def _normalize_text_encoding(self, text):
        normalized = unicodedata.normalize("NFKD", text)
        return normalized.encode("ascii", "ignore").decode("utf-8")
