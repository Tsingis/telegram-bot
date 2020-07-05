import datetime as dt
from scripts.common import set_soup, convert_time_to_localtime


class FormulaOne:
    BASE_URL = "https://www.formula1.com"

    def __init__(self, date=dt.datetime.utcnow()):
        self.date = date

    # Gets top drivers from the latest race and url for more details. Default top 3
    def get_results(self, amount=3):
        results_url = f"{self.BASE_URL}/en/results.html/{self.date.year}/races.html"
        try:
            results_table = self._find_table(results_url)

            # Get race url
            race_results_href = results_table.find_all("a")[-1]["href"]
            race_results_url = self.BASE_URL + race_results_href

            # Get drivers
            results_table = self._find_table(race_results_url)
            drivers = results_table.find_all("tr")[1:amount + 1]

            # Get position, name and time for each driver
            results = []
            for driver in drivers:
                row = [col.text.strip() for col in driver.find_all("td")]
                driver_result = {
                    "name": str(row[3][-3:]),
                    "position": str(row[1]),
                    "time": str(row[-3])
                }
                results.append(driver_result)

            return {
                "results": results,
                "url": race_results_url
            }
        except Exception as ex:
            print("Error getting race results: " + str(ex))
            return None

    # Gets top drivers from overall standings and url for more details. Default top 5
    def get_standings(self, amount=5):
        # Find standings table
        standings_url = f"{self.BASE_URL}/en/results.html/{self.date.year}/drivers.html"
        try:
            table = self._find_table(standings_url)

            # Get drivers
            drivers = table.find_all("tr")[1:amount + 1]

            # Get position, name and points for each driver
            standings = []
            for driver in drivers:
                row = [col.text.strip() for col in driver.find_all("td")]
                driver_standing = {
                    "name": row[2][-3:],
                    "position": row[1],
                    "points": row[-2]
                }
                standings.append(driver_standing)

            return {
                "standings": standings,
                "url": standings_url
            }
        except Exception as ex:
            print("Error getting standings: " + str(ex))
            return None

    # Gets info for the upcoming race
    def get_upcoming(self):
        try:
            soup = set_soup(self.BASE_URL)

            # Get race number
            race_number = self._get_current_race_number()

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
            qualif_time = convert_time_to_localtime(qualif, offset)
            race_time = convert_time_to_localtime(race, offset)

            # Gather info
            race_info = {
                "grandprix": gp,
                "weekend": weekend,
                "country": country,
                "qualifying": qualif_time,
                "race": race_time
            }

            return race_info
        except Exception as ex:
            print("Error getting upcoming race: " + str(ex))
            return None

    def format_results(self, data):
        url = data["url"]
        race = url.split("/")[-2].replace("-", " ").title()

        header = f"Results for {race}:"
        details = f"\n[Details]({url})"
        formatted_results = [f"""{result["position"]}. {result["name"]} {result["time"]}""" for result in data["results"]]

        return f"*{header}*\n" + "\n".join(formatted_results) + details

    def format_standings(self, data):
        url = data["url"]
        race_number = self._get_current_race_number()
        max_races = len(self._get_races())

        header = "Standings:"
        details = f"\n[Details]({url})"

        if (race_number is not None or max_races is not None):
            header = header + f" {(race_number - 1 if race_number < max_races else race_number)}/{max_races}"

        formatted_standings = [f"""{result["position"]}. {result["name"]} - {result["points"]}""" for result in data["standings"]]

        return f"*{header}*\n" + "\n".join(formatted_standings) + details

    def format_upcoming(self, data):
        race_number = self._get_current_race_number()
        max_races = len(self._get_races())

        header = "Upcoming race:"
        if (race_number is not None or max_races is not None):
            header = header + f" {race_number}/{max_races}"

        formatted_raceinfo = (f"""{data["grandprix"]}\n""" +
                              f"""{data["weekend"]} in {data["country"]}\n""" +
                              f"""Qualifying at {data["qualifying"]}\n""" +
                              f"""Race at {data["race"]}""")

        return f"*{header}*\n" + formatted_raceinfo

    # Gets circuit image
    def get_circuit(self, country):
        circuit_name = country.replace(" ", "_")
        url = f"{self.BASE_URL}/en/racing/{self.date.year}/{circuit_name}.html#circuit"
        try:
            soup = set_soup(url)
            data = soup.find("div", {"class": "f1-race-hub--schedule-circuit-map"})

            # Get circuit image url from data
            return data.find("img", {"class": "lazy"})["data-src"]
        except Exception as ex:
            print("Error getting circuit image: " + str(ex))
            return None

    # Find table
    def _find_table(self, url):
        try:
            soup = set_soup(url)
            return soup.find("table", {"class": "resultsarchive-table"})
        except Exception as ex:
            print("Error finding table: " + str(ex))

    # Gets races of current season
    def _get_races(self):
        try:
            soup = set_soup(self.BASE_URL)
            return soup.find_all("article", {"class": "race"})
        except Exception as ex:
            print("Error getting races: " + str(ex))
            return None

    # Gets the number of current race
    def _get_current_race_number(self):
        try:
            races = self._get_races()

            # Get dates for each race
            date_strs = [race.find("time", {"class": "to date-full"}).text.strip() for race in races]
            # Convert date strings to datetime
            dates = [dt.datetime.strptime(date, "%d %b %Y") for date in date_strs]

            # Get race number of the next race.
            race_number = len([value for value in dates if value < self.date and value < dates[-1]]) + 1
            return race_number
        except Exception as ex:
            print("Error getting number of the current race: " + str(ex))
            return None
