import requests
from datetime import datetime
from icalendar import Calendar
import unicodedata
from ..common import convert_timezone
from ...logger import logging


logger = logging.getLogger(__name__)


class FormulaOne:
    CALENDAR_URL = "http://www.formula1.com/calendar/Formula_1_Official_Calendar.ics"

    def __init__(self):
        pass

    def get_race_weekends(self):
        try:
            res = requests.get(self.CALENDAR_URL)
            if res.status_code == 200:
                calendar = Calendar.from_ical(res.content)
                events = [
                    self._event_to_dict(event) for event in calendar.walk("VEVENT")
                ]
                events = self._filter_cancelled_events(events)
                qualifs = self._filter_events_by_type(events, ["qualifying"])
                races = self._filter_events_by_type(events, ["race"])
                race_weekends = self._events_to_race_weekends(qualifs, races)
                return race_weekends
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.exception(f"Error getting data for url: {self.CALENDAR_URL}")

    def _event_to_dict(self, event):
        uid = str(event["UID"])
        return {
            "id": uid.split("@")[-1].strip(),
            "status": str(event["STATUS"]).strip(),
            "type": uid.split("@")[0].strip(),
            "startTime": event["DTSTART"].dt,
            "endTime": event["DTEND"].dt,
            "summary": self._format_text_encoding(event["SUMMARY"]),
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

    def _format_text_encoding(self, text):
        normalized = unicodedata.normalize("NFKD", text)
        return normalized.encode("ascii", "ignore").decode("utf-8")

    def _format_date_utc(self, date):
        date_pattern = "%Y-%m-%dT%H:%M:%S.%f"
        date_tz_adjust = convert_timezone(date=date, source_tz="Europe/London")
        date = date_tz_adjust.strftime(date_pattern)
        return datetime.strptime(date, date_pattern)
