import datetime as dt
from .common import set_soup, convert_time_to_localtime, remove_linebreak_and_whitespace
from ..logger import logging


logger = logging.getLogger(__name__)


class FormulaOne:
    BASE_URL = "https://www.formula1.com"

    def __init__(self, date=dt.datetime.utcnow()):
        self.date = date

    # Gets top drivers from the latest race and url for more details. Default top 3
    def get_results(self, amount=3):
        results_url = f"{self.BASE_URL}/en/results.html/{self.date.year}/races.html"
        try:
            resultsTable = self._find_table(results_url)

            # Get race url
            raceResultsHref = resultsTable.find_all("a")[-1]["href"]
            raceResultsUrl = self.BASE_URL + raceResultsHref

            # Get drivers
            resultsTable = self._find_table(raceResultsUrl)
            drivers = resultsTable.find_all("tr")[1:amount + 1]

            # Get position, name and time for each driver
            results = []
            for driver in drivers:
                row = [col.text.strip() for col in driver.find_all("td")]
                driverResult = {
                    "name": str(row[3][-3:]),
                    "position": str(row[1]),
                    "time": str(row[-3])
                }
                results.append(driverResult)

            return {
                "results": results,
                "url": raceResultsUrl
            }
        except Exception:
            logger.exception("Error getting race results")
            return None

    def format_results(self, data):
        url = data["url"]
        race = url.split("/")[-2].replace("-", " ").title()

        header = f"Results for {race}:"
        details = f"\n[Details]({url})"
        formattedResults = [f"""{result["position"]}. {result["name"]} {result["time"]}""" for result in data["results"]]

        return f"*{header}*\n" + "\n".join(formattedResults) + details

    # Gets top drivers from overall standings and url for more details. Default top 5
    def get_driver_standings(self, amount=5):
        # Find standings table
        standingsUrl = f"{self.BASE_URL}/en/results.html/{self.date.year}/drivers.html"
        try:
            table = self._find_table(standingsUrl)
            # Get drivers
            drivers = table.find_all("tr")[1:amount + 1]

            # Get position, name and points for each driver
            standings = []
            for driver in drivers:
                row = [col.text.strip() for col in driver.find_all("td")]
                driverStanding = {
                    "name": row[2][-3:],
                    "position": row[1],
                    "points": row[-2]
                }
                standings.append(driverStanding)

            return {
                "standings": standings,
                "url": standingsUrl
            }
        except Exception:
            logger.exception("Error getting driver standings")
            return None

    # Gets top teams from overall standings and url for more details. Default top 5
    def get_team_standings(self, amount=5):
        # Find standings table
        standingsUrl = f"{self.BASE_URL}/en/results.html/{self.date.year}/team.html"
        try:
            table = self._find_table(standingsUrl)

            # Get teams
            teams = table.find_all("tr")[1:amount + 1]

            # Get position, name and points for each team
            standings = []
            for team in teams:
                row = [col.text.strip() for col in team.find_all("td")]
                teamNameParts = row[2].split(" ")
                teamStanding = {
                    "name": " ".join(teamNameParts[:2]) if len(teamNameParts) > 2 else teamNameParts[0],
                    "position": row[1],
                    "points": row[-2]
                }
                standings.append(teamStanding)

            return {
                "standings": standings,
                "url": standingsUrl
            }
        except Exception:
            logger.exception("Error getting team standings")
            return None

    def format_standings(self, data):
        url = data["url"]
        race = self._get_current_race()
        raceNumber = race["number"]
        raceDate = race["date"]
        maxRaces = len(self._get_races())

        header = "Standings:"
        details = f"\n[Details]({url})"

        if (raceNumber is not None or maxRaces is not None):
            header = header + f" {(raceNumber - 1 if self.date < raceDate else raceNumber)}/{maxRaces}"

        formattedStandings = [f"""{result["position"]}. {result["name"]} - {result["points"]}""" for result in data["standings"]]

        return f"*{header}*\n" + "\n".join(formattedStandings) + details

    # Gets info for the upcoming race
    def get_upcoming(self):
        try:
            soup = set_soup(self.BASE_URL)
            race = self._get_current_race()
            raceNumber = race["number"]
            raceData = soup.find_all("article", {"class": "race"})[raceNumber - 1]

            # Location, Grand Prix name and url
            location = raceData.find("span", {"class": "name"}).text.title()
            titleElem = raceData.find("h3", {"class": "race-title"})
            gp = titleElem.text
            raceUrl = titleElem.find("a", href=True)["href"]

            # Qualifying and race times
            timesElem = raceData.find_all("time", {"class": "clock-24"})
            qualif = timesElem[-3].text.strip()
            race = timesElem[-1].text.strip()
            offset = timesElem[0]["data-gmt-offset"]

            # Race weekend date range
            start = raceData.find("time", {"class": "from"}).text.strip()
            end = raceData.find("time", {"class": "to"}).text.strip()
            weekend = start[:-5] + " - " + end[:-5]

            # Convert times to local from race time
            qualifTime = convert_time_to_localtime(qualif, offset)
            raceTime = convert_time_to_localtime(race, offset)

            return {
                "grandprix": gp,
                "weekend": weekend,
                "location": location,
                "qualifying": qualifTime,
                "race": raceTime,
                "raceNumber": raceNumber,
                "raceUrl": self.BASE_URL + raceUrl
            }
        except Exception:
            logger.exception("Error getting upcoming race")
            return None

    def format_upcoming(self, data):
        raceNumber = data["raceNumber"]
        maxRaces = len(self._get_races())

        header = "Upcoming race:"
        if (raceNumber is not None or maxRaces is not None):
            header = header + f" {raceNumber}/{maxRaces}"

        formattedRaceInfo = (f"""{data["grandprix"]}\n""" +
                             f"""{data["weekend"]} in {data["location"]}\n""" +
                             f"""Qualifying at {data["qualifying"]}\n""" +
                             f"""Race at {data["race"]}""")

        return f"*{header}*\n" + formattedRaceInfo

    # Gets circuit image
    def get_circuit(self, raceUrl):
        try:
            soup = set_soup(raceUrl)
            data = soup.find("div", {"class": "f1-race-hub--schedule-circuit-map"})
            return data.find("img", {"class": "lazy"})["data-src"]
        except Exception:
            logger.exception("Error getting circuit image")
            return None

    # Find table
    def _find_table(self, url):
        try:
            soup = set_soup(url)
            return soup.find("table", {"class": "resultsarchive-table"})
        except Exception:
            logger.exception("Error finding table")

    # Gets races of current season
    def _get_races(self):
        try:
            soup = set_soup(self.BASE_URL)
            return soup.find_all("article", {"class": "race"})
        except Exception:
            logger.exception("Error getting races")
            return None

    # Gets the number of current race
    def _get_current_race(self):
        try:
            races = self._get_races()
            dateDetails = [race.find("p", {"class": "race-date-full"}).text for race in races]
            dateStrs = [remove_linebreak_and_whitespace(detail).split("-")[-1] for detail in dateDetails]
            dates = [dt.datetime.strptime(date, "%d%b%Y") if date != "TBC" else self.date.replace(month=12, day=31) for date in dateStrs]

            # Get race number of the next race.
            raceNumber = len([value for value in dates if value < self.date and value < dates[-1]]) + 1
            return {
                "number": raceNumber,
                "date": dates[raceNumber - 1]
            }
        except Exception:
            logger.exception("Error getting number of the current race")
            return None
