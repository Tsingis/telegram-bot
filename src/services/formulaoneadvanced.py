from datetime import datetime
from .formulaonebase import FormulaOne
from .common import convert_timezone, set_soup
from ..logger import logging


logger = logging.getLogger(__name__)


class FormulaOneAdvanced(FormulaOne):
    BASE_URL = "https://www.formula1.com"

    def __init__(self, date=datetime.utcnow()):
        super().__init__()
        self.date = date
        self.races = sorted(self.get_race_data(), key=lambda x: x["raceTime"])
        self.racesAmount = len(self.races)

    # Gets top drivers from the latest race and url for more details. Default top 3
    def get_results(self, amount=3):
        results_url = f"{self.BASE_URL}/en/results.html/{self.date.year}/races.html"
        try:
            resultsTable = self.find_table(results_url)

            # Get race url
            raceResultsHref = resultsTable.find_all("a")[-1]["href"]
            raceResultsUrl = self.BASE_URL + raceResultsHref

            # Get drivers
            resultsTable = self.find_table(raceResultsUrl)
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
        formattedResults = [
            f"""{result["position"]}. {result["name"]} {result["time"]}""" for result in data["results"]]
        return f"*{header}*\n" + "\n".join(formattedResults) + details

    # Gets top drivers from overall standings and url for more details. Default top 5
    def get_driver_standings(self, amount=5):
        # Find standings table
        standingsUrl = f"{self.BASE_URL}/en/results.html/{self.date.year}/drivers.html"
        try:
            table = self.find_table(standingsUrl)
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
            table = self.find_table(standingsUrl)
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
        upcoming = self.get_upcoming()
        raceNumber = upcoming["raceNumber"]
        if (self.date <= upcoming["raceTime"]):
            raceNumber -= 1

        header = f"""Standings: {raceNumber}/{self.racesAmount}"""
        details = f"""\n[Details]({url})"""

        formattedStandings = [
            f"""{result["position"]}. {result["name"]} - {result["points"]}""" for result in data["standings"]]
        return f"*{header}*\n" + "\n".join(formattedStandings) + details

    # Gets info for the upcoming race
    def get_upcoming(self):
        try:
            race = next((
                race for race in self.races if race["raceTime"] >= self.date), self.races[-1])
            return race
        except Exception:
            logger.exception("Error getting upcoming race")
            return None

    def format_upcoming(self, data):
        data["raceName"] = "TEST"
        data["qualifyingTime"] = self.format_date(
            data["qualifyingTime"])
        data["raceTime"] = self.format_date(
            data["raceTime"])
        header = f"""Upcoming race: {data["raceNumber"]}/{self.racesAmount}"""
        formattedRaceInfo = (f"""{data["raceName"]}\n""" +
                             f"""{data["location"]}\n""" +
                             f"""Qualifying on {data["qualifyingTime"]}\n""" +
                             f"""Race on {data["raceTime"]}""")
        return f"*{header}*\n" + formattedRaceInfo

    def find_circuit_image(self, url):
        try:
            # Find image url container
            soup = set_soup(url)
            imgUrlContainer = soup.find(
                "div", {"class": "f1-race-hub--schedule-circuit-map"})
            imgUrl = imgUrlContainer.find("a")["href"]

            # Find image from container
            soupTwo = set_soup(self.BASE_URL + imgUrl)
            imgContainer = soupTwo.find(
                "div", {"class": "f1-race-hub--map-container"})
            return imgContainer.find("img", {"class": "lazy"})["data-src"]
        except Exception:
            logger.exception("Error getting circuit image")
            return None

    # Find table from page
    def find_table(self, url):
        try:
            soup = set_soup(url)
            return soup.find("table", {"class": "resultsarchive-table"})
        except Exception:
            logger.exception("Error finding table")

    # Formats date with given input and output patterns
    def format_date(self, date):
        pattern = "%a %B %d at %H:%M"
        date = convert_timezone(date, None, "Europe/Helsinki")
        return datetime.strftime(date, pattern)
