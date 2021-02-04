import requests
import googlemaps
import os
from ..logger import logging


logger = logging.getLogger(__name__)


class WeatherSearch:

    GOOGLE_API_KEY = os.environ["GOOGLE_API"]
    DARKSKY_API_KEY = os.environ["DARKSKY_API"]

    def __init__(self):
        self.gmaps = googlemaps.Client(key=self.GOOGLE_API_KEY)

    # Get specific weather data for given coords
    def get_data(self, location):
        try:
            coords = self._get_coords(location)
            url = (f"""https://api.darksky.net/forecast/{self.DARKSKY_API_KEY}/"""
                   f"""{coords["lat"]},{coords["lng"]}""")
            params = {
                "units": "si",
                "exclude": "minutely,hourly,daily,alerts,flags"
            }

            res = requests.get(url=url, params=params)
            if (res.status_code == 200):
                return res.json()
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.exception(f"Error getting weather data for location: {location}")
            return None

    def format_info(self, data, location):
        current = data["currently"]
        info = {
            "Summary": current["summary"],
            "Temp": str(round(current["temperature"], 1)) + " C",
            "Wind": str(round(current["windSpeed"], 2)) + " m/s",
            "Hum": str(int(round(current["humidity"] * 100, 0))) + " %",
            "Pres": str(int(round(current["pressure"], 0))) + " hPa",
            "Clouds": str(int(round(current["cloudCover"] * 100, 0))) + " %"
        }

        if ("precipType" in current):
            info["Precip"] = current["precipType"]
            info["Amount"] = str(round(current["precipIntensity"], 2)) + " mm/h"

        header = f"*Weather for {location.capitalize()}:*\n"
        formatted_info = "\n".join([f"{key}: {value}" for (key, value) in info.items()])
        return header + formatted_info + "\n\n*Powered by Dark Sky*"

    # Get coordinates for given location
    def _get_coords(self, location):
        try:
            result = self.gmaps.geocode(location)
            return result[0]["geometry"]["location"]
        except Exception:
            logger.exception(f"Error getting coordinates for location: {location}")
