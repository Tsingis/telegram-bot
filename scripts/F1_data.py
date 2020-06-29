import datetime as dt
from scripts.common_helper import set_soup, timezone_difference


BASE_URL = "https://www.formula1.com"
CURRENT_DATE = dt.datetime.utcnow()


# Find table
def find_table(url):
    soup = set_soup(url)
    return soup.find("table", {"class": "resultsarchive-table"})


# Time conversion from race time to local time
def convert_time(time, offset):
    time = dt.datetime.strptime(time, "%H:%M")

    # Add or subtract hours based on offset
    if offset[0] == "+":
        time = time - dt.timedelta(hours=int(offset[1:].split(":")[0]))
    else:
        time = time + dt.timedelta(hours=int(offset[1:].split(":")[0]))

    # Time difference between timezones
    hours = timezone_difference()

    # Convert datetime to HH:MM format
    return (time + dt.timedelta(hours=hours)).strftime("%H:%M")


# Find circuit image
def get_circuit(country):
    circuit_name = country.replace(" ", "_")
    url = f"{BASE_URL}/en/racing/{CURRENT_DATE.year}/{circuit_name}.html#circuit"
    soup = set_soup(url)

    data = soup.find("div", {"class": "f1-race-hub--schedule-circuit-map"})

    # Get circuit image url from data
    return data.find("img", {"class": "lazy"})["data-src"]


# Finds the current race
def get_race():
    try:
        soup = set_soup(BASE_URL)

        # Get info of all races
        races = soup.find_all("article", {"class": "race"})

        # Get dates for each race
        dates = [race.find("time", {"class": "to date-full"}).text.strip() for race in races]

        # Convert dates to datetime objects
        dates = [dt.datetime.strptime(date, "%d %b %Y") for date in dates]

        # Get race number of the next race. +1 to adjust indexing
        race_number = len([value for value in dates if value < CURRENT_DATE and value < dates[-1]]) + 1

        return race_number, len(races)
    except Exception:
        return None, None


# Gets top3 drivers from the latest race and url for more details
def get_results():
    # Find results table
    results_url = f"{BASE_URL}/en/results.html/{CURRENT_DATE.year}/races.html"
    try:
        results_table = find_table(results_url)

        # Find race url
        race_results_href = results_table.find_all("a")[-1]["href"]
        race_results_url = BASE_URL + race_results_href

        # Find top 3 drivers
        race_table = find_table(race_results_url)
        drivers = race_table.find_all("tr")[1:4]

        # Get position, name and time for each driver
        results = []
        for driver in range(len(drivers)):
            data = drivers[driver].find_all("td")
            row = [col.text.strip() for col in data]
            position = str(row[1])
            name = str(row[3][-3:])
            time = str(row[-3])
            result = f"{position}. {name} {time}"
            results.append(result)

        return race_results_url, results
    except Exception:
        return None, None


# Gets top5 drivers from overall standings and url for more details
def get_standings():
    # Find standings table
    standings_url = f"{BASE_URL}/en/results.html/{CURRENT_DATE.year}/drivers.html"
    try:
        table = find_table(standings_url)

        # Find top 5 drivers
        drivers = table.find_all("tr")[1:6]

        # Get position, name and points for each driver
        standings = []
        for driver in range(len(drivers)):
            data = drivers[driver].find_all("td")
            row = [col.text.strip() for col in data]
            position = row[1]
            name = row[2][-3:]
            points = row[-2]
            result = f"{position}. {name} - {points}"
            standings.append(result)

        return standings_url, standings
    except Exception:
        return None, None


# Gets info for the next race
def get_upcoming():
    soup = set_soup(BASE_URL)
    try:
        # Get race number
        race_number, _ = get_race()

        # Find race data for upcoming race
        race_data = soup.find_all("article", {"class": "race"})[race_number - 1]

        # Find url for country name and Grand Prix name
        country = race_data.find("span", {"class": "name"}).text.title()
        gp = race_data.find("h3", {"class": "race-title"}).text

        # Find qualifying and race times
        qualif = race_data.find_all("time", {"class": "clock-24"})[-3].text.strip()
        race = race_data.find_all("time", {"class": "clock-24"})[-1].text.strip()

        # Find race weekend date range
        start = race_data.find("time", {"class": "from"}).text.strip()
        end = race_data.find("time", {"class": "to"}).text.strip()
        weekend = start[:-5] + " - " + end[:-5]

        # Find time offset from UTC
        offset = race_data.find("time", {"class": "clock-24"})["data-gmt-offset"]

        # Convert times to local from race time
        qualif = convert_time(qualif, offset)
        race = convert_time(race, offset)

        # Gather info
        race_info = {
            "grandprix": gp,
            "weekend": weekend,
            "country": country,
            "qualifying": qualif,
            "race": race
        }

        try:
            circuit_img = get_circuit(country)
        except Exception:
            circuit_img = get_circuit(country.lower())

        return race_info, circuit_img
    except Exception:
        return None, None
