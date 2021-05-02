import requests
import googlemaps
import os
from ..logger import logging


logger = logging.getLogger(__name__)


class WeatherSearch:
    GOOGLE_API_KEY = os.environ["GOOGLE_API"]
    OPENWEATHER_API_KEY = os.environ["OPENWEATHER_API"]

    def __init__(self):
        self.gmaps = googlemaps.Client(key=self.GOOGLE_API_KEY)

    # Get specific weather data for given location
    def get_info(self, location):
        try:
            coords = self._get_coords(location)
            url = ("https://api.openweathermap.org/data/2.5/weather?" +
                   f"""lat={coords["lat"]}&lon={coords["lng"]}""" +
                   f"""&units=metric&appid={self.OPENWEATHER_API_KEY}""")
            res = requests.get(url).json()
            data = {
                "description": res["weather"][0]["description"],
                "temperature": round(res["main"]["temp"], 1),
                "wind": round(res["wind"]["speed"], 2),
                "humidity": int(round(res["main"]["humidity"], 0)),
                "pressure": int(round(res["main"]["pressure"], 0)),
                "clouds": int(round(res["clouds"]["all"], 0)),
                "icon": res["weather"][0]["icon"]
            }

            if ("snow" in res):
                data["precipType"] = "snow"
                data["amount"] = round(res["snow"]["1h"], 2)

            if ("rain" in res):
                data["precipType"] = "rain"
                data["amount"] = round(res["rain"]["1h"], 2)

            return data
        except Exception:
            return None

    def format_info(self, data, location):
        info = {
            "Desc": data["description"].capitalize(),
            "Temp": str(data["temperature"]) + " °C",
            "Wind": str(data["wind"]) + " m/s",
            "Hum": str(data["humidity"]) + " %",
            "Pres": str(data["pressure"]) + " hPa",
            "Clouds": str(data["clouds"]) + " %",
        }

        if ("precipType" in data):
            info["Precip"] = data["precipType"]
            info["Amount"] = str(data["amount"]) + " mm/h"

        header = f"*Weather for {location.title()}*\n"
        return header + "\n".join([f"{key}: {value}" for (key, value) in info.items()])

    # Get icon for weather
    def get_icon_url(self, data):
        try:
            return f"""https://openweathermap.org/img/wn/{data["icon"]}@4x.png"""
        except Exception:
            logger.exception(f"Error getting weather icon for data: {data}")
            return None

    # Get coordinates for given location
    def _get_coords(self, location):
        try:
            result = self.gmaps.geocode(location)
            return result[0]["geometry"]["location"]
        except Exception:
            logger.exception(
                f"Error getting coordinates for location: {location}")
