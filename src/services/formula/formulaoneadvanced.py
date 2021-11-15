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
        self.race_weekends = self.get_race_weekends()
        self.races_amount = len(self.race_weekends)

    # Gets top drivers from the latest race and url for more details. Default top 3
    def get_results(self, amount=3):
        url = f"{self.BASE_URL}/en/results.html/{self.date.year}/races.html"
        try:
            results_table = self._find_table(url)
            results_href = results_table.find_all("a")[-1]["href"]
            results_url = self.BASE_URL + results_href

            results_table = self._find_table(results_url)
            rows = results_table.find_all("tr")[1 : amount + 1]
            driver_rows = [
                [cell.text.strip() for cell in row.find_all("td")] for row in rows
            ]
            results = [
                {
                    "name": row[3],
                    "position": int(row[1]),
                    "time": row[-3],
                }
                for row in driver_rows
            ]
            return {"results": results, "url": results_url}
        except Exception:
            logger.exception("Error getting race results")

    def format_results(self, data):
        url = data["url"]
        race = url.split("/")[-2].replace("-", " ").title()
        header = f"Results for {race}:"
        details = f"\n[Details]({url})"
        formatted_results = [
            f"""{result["position"]}. {result["name"][-3:]} {result["time"]}"""
            for result in data["results"]
        ]
        return f"*{header}*\n" + "\n".join(formatted_results) + details

    # Gets top drivers from overall standings and url for more details. Default top 5
    def get_driver_standings(self, amount=5):
        url = f"{self.BASE_URL}/en/results.html/{self.date.year}/drivers.html"
        try:
            table = self._find_table(url)
            rows = table.find_all("tr")[1 : amount + 1]
            driver_rows = [
                [cell.text.strip() for cell in row.find_all("td")] for row in rows
            ]
            standings = [
                {
                    "driver": row[2],
                    "position": int(row[1]),
                    "points": self._format_number(float(row[-2])),
                }
                for row in driver_rows
            ]
            return {"driverStandings": standings, "driverUrl": url}
        except Exception:
            logger.exception("Error getting driver standings")

    # Gets top teams from overall standings and url for more details. Default top 5
    def get_team_standings(self, amount=5):
        url = f"{self.BASE_URL}/en/results.html/{self.date.year}/team.html"
        try:
            table = self._find_table(url)
            rows = table.find_all("tr")[1 : amount + 1]
            team_rows = [
                [cell.text.strip() for cell in row.find_all("td")] for row in rows
            ]
            standings = [
                {
                    "team": row[2],
                    "position": int(row[1]),
                    "points": self._format_number(float(row[-2])),
                }
                for row in team_rows
            ]
            return {"teamStandings": standings, "teamUrl": url}
        except Exception:
            logger.exception("Error getting team standings")

    def format_standings(self, data):
        upcoming = self.get_upcoming()
        race_number = upcoming["raceNumber"]
        if self.date <= upcoming["raceTime"]:
            race_number -= 1

        header = f"""Standings {race_number}/{self.races_amount}"""
        driver_details = f"""\n[Details]({data["driverUrl"]})"""
        team_details = f"""\n[Details]({data["teamUrl"]})"""

        for standing in data["teamStandings"]:
            team_name_parts = standing["team"].split(" ")
            if len(team_name_parts) > 2:
                standing["team"] = " ".join(team_name_parts[:2])
            else:
                standing["team"] = team_name_parts[0]

        driver_standings = [
            f"""{result["position"]}. {result["driver"][-3:]} - {result["points"]}"""
            for result in data["driverStandings"]
        ]
        team_standings = [
            f"""{result["position"]}. {result["team"]} - {result["points"]}"""
            for result in data["teamStandings"]
        ]
        formatted_standings = (
            "*Drivers*:\n"
            + "\n".join(driver_standings)
            + driver_details
            + "\n\n*Teams*:\n"
            + "\n".join(team_standings)
            + team_details
        )
        return f"*{header}*\n" + formatted_standings

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

    def _find_table(self, url):
        try:
            soup = set_soup(url)
            return soup.find("table", {"class": "resultsarchive-table"})
        except Exception:
            logger.exception("Error finding table")

    # Formats date with specific input and output patterns
    def _format_date(self, date):
        pattern = "%a %B %d at %H:%M"
        date = convert_timezone(date=date, target_tz="Europe/Helsinki")
        return datetime.strftime(date, pattern)

    # Formats floating number without insignificant trailing zeroes
    def _format_number(self, number):
        return f"{number:g}"
