import os
from datetime import datetime
from ..utils import get
from ...logger import logging


logger = logging.getLogger(__name__)


class FormulaOneBase:
    REGION = os.environ["REGION"]
    GOOGLE_API_KEY = os.environ["GOOGLE_API"]
    F1_CALENDAR_URL = os.environ["F1_CALENDAR_URL"]

    def __init__(self, date=datetime.utcnow()):
        self.date = date
        self.source_datetime_pattern = "%Y-%m-%dT%H:%M:%SZ"
        self.race_weekends = self._get_race_weekends()
        self.races_amount = len(self.race_weekends)

    def _get_race_weekends(self):
        """
        Parse and combine scheduled qualifying, sprint and race events to race weekends
        """
        try:
            res = get(self.F1_CALENDAR_URL)
            data = res.json()
            if not data:
                logger.warning(f"No events available for year {self.date.year}")
                return
            race_weekends = [
                self._event_to_race_weekend(event) for event in data["races"]
            ]
            return race_weekends
        except Exception:
            logger.exception(
                f"Error getting calendar data with url {self.F1_CALENDAR_URL}"
            )

    def _event_to_race_weekend(self, event):
        country = self._find_country(event["latitude"], event["longitude"])
        race_weekend = {
            "round": event["round"],
            "name": event["name"],
            "country": country,
            "location": event["location"],
            "raceUrl": self._get_race_url(country),
            "sessions": {},
        }

        if not race_weekend["name"].lower().endswith("grand prix"):
            race_weekend["name"] = race_weekend["name"] + " Grand Prix"

        for session, date in event["sessions"].items():
            if session == "gp":
                key = "race"
            elif session == "qualifying":
                key = "qualif"
            else:
                key = session
            race_weekend["sessions"][key] = self._string_to_datetime(date)

        return race_weekend

    def _get_race_url(self, country):
        base_url = "https://www.formula1.com/en/racing"
        return f"""{base_url}/{self.date.year}/{country.replace(" ", "_")}.html"""

    def _find_country(self, lat, lng):
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "key": self.GOOGLE_API_KEY,
                "latlng": f"{lat},{lng}",
                "region": self.REGION.lower(),
            }
            data = get(url, params).json()
            components = data["results"][0]["address_components"]
            country = next(
                (
                    component["long_name"].title()
                    for component in components
                    if "country" in component["types"]
                ),
                None,
            )
            return country
        except Exception:
            logger.exception(
                f"Error getting country for latitude {lat} and longitude {lng}"
            )

    def _string_to_datetime(self, date):
        return datetime.strptime(date, self.source_datetime_pattern)
