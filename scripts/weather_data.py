import requests
import googlemaps
import os


GOOGLE_API_KEY = os.environ["GOOGLE_API"]
DARKSKY_API_KEY = os.environ["DARKSKY_API"]

gmaps = googlemaps.Client(key=GOOGLE_API_KEY)


# Get specific weather data for given location
def get_data(location):
    try:
        result = gmaps.geocode(location)
        coords = result[0]["geometry"]["location"]

        url = (f"""https://api.darksky.net/forecast/{DARKSKY_API_KEY}/"""
               f"""{coords["lat"]},{coords["lng"]}""")
        params = {
            "units": "si",
            "exclude": "minutely,hourly,daily,alerts,flags"
        }

        res = requests.get(url=url, params=params) 
        data = res.json()["currently"]

        info = {
            "Summary": data["summary"],
            "Temp": str(round(data["temperature"], 1)) + " C",
            "Wind": str(round(data["windSpeed"], 2)) + " m/s",
            "Hum": str(int(round(data["humidity"] * 100, 0))) + " %",
            "Pres": str(int(round(data["pressure"], 0))) + " hPa",
            "Clouds": str(int(round(data["cloudCover"] * 100, 0))) + " %"
        }

        if ("precipType" in data):
            info["Precip"] = data["precipType"]
            info["Amount"] = str(round(data["precipIntensity"], 2)) + " mm/h"

        return info
    except Exception:
        return None
