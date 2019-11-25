import xml.etree.ElementTree as ET
import urllib.request as request
import datetime as dt
import json
import os
import re


fmi_apikey = os.environ["FMI_API"]


# Parses times and values from XML for timevaluepair format
def parse_timeseries(series):
    return [(item1.text, item2.text) for item1, item2 in
            zip(series.iter(tag="{http://www.opengis.net/waterml/2.0}time"),
                series.iter(tag="{http://www.opengis.net/waterml/2.0}value"))]


# Parses keynames from XML
def parse_keynames(series):
    return [item.attrib.get("{http://www.opengis.net/gml/3.2}id").split("-")[-1]
            for item in series]


# Finds specific station for given location
def get_station(location):
    # Load stations
    with open("static/weather_stations.json", "r", encoding="utf-8") as file:
        stations = json.load(file)

    # Look for station in given location
    if (location.capitalize() in stations):
        return stations[location.capitalize()]


# Data for given weather station
def get_data(station):
    # Get current time - 20 minutes to always get the latest observation
    start = (dt.datetime.utcnow() - dt.timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Define url
    url = (f"http://data.fmi.fi/fmi-apikey/{fmi_apikey}"
           f"/wfs?request=getFeature&storedquery_id=fmi::observations::"
           f"weather::timevaluepair&fmisid={station}&starttime={start}")

    # Get data
    try:
        req = request.urlopen(url)
        if (req.getcode() == 200):
            xml = req.read().decode("utf-8")
            tree = ET.ElementTree(ET.fromstring(xml))

            # Data model: MeasurementTimeseries
            tag = "{http://www.opengis.net/waterml/2.0}MeasurementTimeseries"

            # Keys
            # keys = parse_keynames(tree.iter(tag=tag))[:-1]  # original keys
            keys = ["Temp", "Wind", "Gust", "Wind dir", "Hum", "Temp dew",
                    "Rain int", "Rain", "Snow", "Pres", "Vis", "Cloud"]

            # Choose latest values
            timevalues = [parse_timeseries(series) for series in tree.iter(tag=tag)]
            values = [value[-1][1] for value in timevalues]

            # Complete data
            data = dict(zip(keys, values))

            # Replace negative snow value with NaN
            data.update({"Snow": "NaN" if float(data["Snow"]) <= 0 else data["Snow"]})

            # Format data
            data = [
                "Temp: " + data["Temp"] + " C",
                "Wind: " + data["Wind"] + " m/s",
                "Hum: " + data["Hum"].split(".")[0] + " %",
                "Rain: " + data["Rain"] + " mm",
                "Snow: " + data["Snow"] + " cm",
                "Clouds: " + data["Cloud"].split(".")[0] + "/8"
            ]

            # Return "Not available" if info is missing
            return [result.split(":")[0] + ": Not available" if re.search("NaN", result) is not None else result for result in data]
    except Exception:
        return None
