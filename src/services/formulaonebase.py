
import requests
from datetime import datetime
from icalendar import Calendar
from .common import convert_timezone
from ..logger import logging


logger = logging.getLogger(__name__)


class FormulaOne():
    CALENDAR_URL = "http://www.formula1.com/calendar/Formula_1_Official_Calendar.ics"

    def __init__(self):
        self.datePattern = "%Y-%m-%dT%H:%M:%S.%f"

    def get_race_data(self):
        try:
            res = requests.get(self.CALENDAR_URL)
            if res.status_code == 200:
                calendar = Calendar.from_ical(res.text)
                events = [self.event_to_dict(event)
                          for event in calendar.walk("VEVENT")]
                qualifs = self.filter_events_by_type(events, ["qualifying"])
                races = self.filter_events_by_type(events, ["race"])
                raceData = self.events_to_race_weekends(qualifs, races)
                return raceData
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.exception(
                f"Error getting data for url: {self.CALENDAR_URL}")
            return None

    def event_to_dict(self, event):
        uid = str(event["UID"])
        return {
            "id": uid.split("@")[-1].strip(),
            "type": uid.split("@")[0].strip(),
            "startTime": event["DTSTART"].dt,
            "endTime": event["DTEND"].dt,
            "summary": str(event["SUMMARY"]).strip(),
            "description": str(event["DESCRIPTION"]).strip(),
            "location": str(event["LOCATION"]).strip()
        }

    def events_to_race_weekends(self, qualifs, races):
        raceWeekends = []
        for index, race in enumerate(races):
            qualif = next((
                qualif for qualif in qualifs if qualif["id"] == race["id"]), None)
            if (qualif is None):
                raise Exception("No matching race and qualifying events")
            raceWeekend = {
                "raceNumber": index + 1,
                "raceName": race["summary"].split("-")[0].strip(),
                "qualifyingTime": self.format_date_utc(qualif["startTime"]),
                "raceTime": self.format_date_utc(race["startTime"]),
                "raceUrl": self.find_race_url(race["description"]),
                "location": race["location"],
            }
            raceWeekends.append(raceWeekend)
        return raceWeekends

    def filter_events_by_type(self, events, types):
        return [
            event for event in events
            if any(keyword.lower() in event["type"].lower() for keyword in types)
        ]

    def find_race_url(self, text):
        pattern = "https://www.formula1.com/en/racing"
        return next((word for word in text.split(" ") if word.startswith(pattern)), pattern)

    def format_date_utc(self, date):
        dateTzAdjust = convert_timezone(date, "Europe/London")
        date = dateTzAdjust.strftime(self.datePattern)
        return datetime.strptime(date, self.datePattern)
