from datetime import datetime
from .formulaonebase import FormulaOne
from ..common import convert_timezone, set_soup
from ...logger import logging


logger = logging.getLogger(__name__)


class FormulaOneAdvanced(FormulaOne):
    BASE_URL = "https://www.formula1.com"

    def __init__(self, date=datetime.utcnow()):
        super().__init__()
        self.date = date
        self.race_weekends = sorted(
            self.get_race_weekends(), key=lambda x: x["raceTime"]
        )
        self.races_amount = len(self.race_weekends)

    # Gets top drivers from the latest race and url for more details. Default top 3
    def get_results(self, amount=3):
        url = f"{self.BASE_URL}/en/results.html/{self.date.year}/races.html"
        try:
            results_table = self._find_table(url)

            # Get race url
            results_href = results_table.find_all("a")[-1]["href"]
            results_url = self.BASE_URL + results_href

            # Get drivers
            results_table = self._find_table(results_url)
            drivers = results_table.find_all("tr")[1 : amount + 1]

            # Get position, name and time for each driver
            results = []
            for driver in drivers:
                row = [col.text.strip() for col in driver.find_all("td")]
                result = {
                    "name": str(row[3][-3:]),
                    "position": str(row[1]),
                    "time": str(row[-3]),
                }
                results.append(result)
            return {"results": results, "url": results_url}
        except Exception:
            logger.exception("Error getting race results")

    def format_results(self, data):
        url = data["url"]
        race = url.split("/")[-2].replace("-", " ").title()
        header = f"Results for {race}:"
        details = f"\n[Details]({url})"
        formatted_results = [
            f"""{result["position"]}. {result["name"]} {result["time"]}"""
            for result in data["results"]
        ]
        return f"*{header}*\n" + "\n".join(formatted_results) + details

    # Gets top drivers from overall standings and url for more details. Default top 5
    def get_driver_standings(self, amount: int = 5):
        url = f"{self.BASE_URL}/en/results.html/{self.date.year}/drivers.html"
        try:
            table = self._find_table(url)
            drivers = table.find_all("tr")[1 : amount + 1]

            # Get position, name and points for each driver
            standings = []
            for driver in drivers:
                row = [col.text.strip() for col in driver.find_all("td")]
                standing = {
                    "name": row[2][-3:],
                    "position": row[1],
                    "points": row[-2],
                }
                standings.append(standing)
            return {"standings": standings, "url": url}
        except Exception:
            logger.exception("Error getting driver standings")

    # Gets top teams from overall standings and url for more details. Default top 5
    def get_team_standings(self, amount=5):
        url = f"{self.BASE_URL}/en/results.html/{self.date.year}/team.html"
        try:
            table = self._find_table(url)
            teams = table.find_all("tr")[1 : amount + 1]

            # Get position, name and points for each team
            standings = []
            for team in teams:
                row = [col.text.strip() for col in team.find_all("td")]
                team_name_parts = row[2].split(" ")
                standing = {
                    "name": " ".join(team_name_parts[:2])
                    if len(team_name_parts) > 2
                    else team_name_parts[0],
                    "position": row[1],
                    "points": row[-2],
                }
                standings.append(standing)
            return {"standings": standings, "url": url}
        except Exception:
            logger.exception("Error getting team standings")

    def format_standings(self, data):
        url = data["url"]
        upcoming = self.get_upcoming()
        race_number = upcoming["raceNumber"]
        if self.date <= upcoming["raceTime"]:
            race_number -= 1

        header = f"""Standings: {race_number}/{self.races_amount}"""
        details = f"""\n[Details]({url})"""

        formatted_standings = [
            f"""{result["position"]}. {result["name"]} - {result["points"]}"""
            for result in data["standings"]
        ]
        return f"*{header}*\n" + "\n".join(formatted_standings) + details

    # Gets info for the upcoming race
    def get_upcoming(self):
        try:
            race = next(
                (race for race in self.race_weekends if race["raceTime"] >= self.date),
                self.race_weekends[-1],
            )
            return race
        except Exception:
            logger.exception("Error getting upcoming race")

    def format_upcoming(self, data):
        data["qualifyingTime"] = self._format_date(data["qualifyingTime"])
        data["raceTime"] = self._format_date(data["raceTime"])
        header = f"""Upcoming race: {data["raceNumber"]}/{self.races_amount}"""
        formatted_race_info = (
            f"""{data["raceName"]}\n"""
            + f"""{data["location"]}\n"""
            + f"""Qualifying on {data["qualifyingTime"]}\n"""
            + f"""Race on {data["raceTime"]}"""
        )
        return f"*{header}*\n" + formatted_race_info

    def find_circuit_image(self, url):
        try:
            soup = set_soup(url)
            img_url_container = soup.find(
                "div", {"class": "f1-race-hub--schedule-circuit-map"}
            )
            img_url = img_url_container.find("a")["href"]
            soup = set_soup(self.BASE_URL + img_url)
            img_container = soup.find("div", {"class": "f1-race-hub--map-container"})
            return img_container.find("img", {"class": "lazy"})["data-src"]
        except Exception:
            logger.exception("Error getting circuit image")

    # Find table from page
    def _find_table(self, url):
        try:
            soup = set_soup(url)
            return soup.find("table", {"class": "resultsarchive-table"})
        except Exception:
            logger.exception("Error finding table")

    # Formats date with given input and output patterns
    def _format_date(self, date):
        pattern = "%a %B %d at %H:%M"
        date = convert_timezone(date=date, target_tz="Europe/Helsinki")
        return datetime.strftime(date, pattern)
