import os
from ..common.logger import logging
from ..common.utils import get, format_as_header, format_as_code


logger = logging.getLogger(__name__)


class WeatherSearch:
    GOOGLE_API_KEY = os.environ["GOOGLE_API"]
    OPENWEATHER_API_KEY = os.environ["OPENWEATHER_API"]
    REGION = os.environ["REGION"]

    def __init__(self):
        pass

    # Get specific weather data for given location
    def get_info(self, location):
        try:
            coords = self._get_coords(location)
            if coords is None:
                return
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": coords["lat"],
                "lon": coords["lng"],
                "units": "metric",
                "appid": self.OPENWEATHER_API_KEY,
            }
            data = get(url, params).json()
            info = {
                "description": data["weather"][0]["description"],
                "temperature": round(data["main"]["temp"], 1),
                "wind": round(data["wind"]["speed"], 2),
                "humidity": int(round(data["main"]["humidity"], 0)),
                "pressure": int(round(data["main"]["pressure"], 0)),
                "clouds": int(round(data["clouds"]["all"], 0)),
                "icon": data["weather"][0]["icon"],
            }

            if "snow" in data:
                info["precipType"] = "snow"
                info["amount"] = round(data["snow"]["1h"], 2)

            if "rain" in data:
                info["precipType"] = "rain"
                info["amount"] = round(data["rain"]["1h"], 2)
            return info
        except Exception:
            logger.exception(f"Error getting info for location {location}")

    def format_info(self, data, location):
        info = {
            "desc": data["description"].capitalize(),
            "temp": str(data["temperature"]) + " °C",
            "wind": str(data["wind"]) + " m/s",
            "hum": str(data["humidity"]) + " %",
            "pres": str(data["pressure"]) + " hPa",
            "cloud": str(data["clouds"]) + " %",
        }

        if "precipType" in data:
            info["precip"] = data["precipType"]
            info["amount"] = str(data["amount"]) + " mm/h"

        header = f"Weather in {location.title()}:"
        body = "\n".join(
            [
                f"{key.capitalize()}:".ljust(7) + f"{value}"
                for (key, value) in info.items()
            ]
        )
        return format_as_header(header) + "\n" + format_as_code(body)

    # Get icon for weather
    def get_icon_url(self, data):
        try:
            return f"""https://openweathermap.org/img/wn/{data["icon"]}@4x.png"""
        except Exception:
            logger.exception(f"Error getting weather icon for data {data}")

    # Get coordinates for given location
    def _get_coords(self, location):
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "key": self.GOOGLE_API_KEY,
                "address": location,
                "region": self.REGION.lower(),
            }
            data = get(url, params).json()
            if not data["results"]:
                logger.info(f"No coordinates found with {location}")
                return
            coords = data["results"][0]["geometry"]["location"]
            return coords
        except Exception:
            logger.exception(f"Error getting coordinates for location {location}")
