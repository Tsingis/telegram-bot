from datetime import datetime
from .formulaonebase import FormulaOneBase
from ..common.logger import logging
from ..common.utils import set_soup


logger = logging.getLogger(__name__)


class FormulaOneAdvanced(FormulaOneBase):
    BASE_URL = "https://www.formula1.com"

    def __init__(self):
        super().__init__()

    def get_results(self, amount=10):
        """
        Gets top drivers from the latest race and url for more details
        """
        url = f"{self.BASE_URL}/en/results.html/{self.date.year}/races.html"
        try:
            soup = set_soup(url)
            races_table = soup.find("table", {"class": "resultsarchive-table"})
            if races_table is None:
                logger.info(f"Races table not found for year {self.date.year}")
                return
            race_results = races_table.find_all("a")
            if not race_results:
                logger.info(f"No past races found for year {self.date.year}")
                return
            results_url = self.BASE_URL + race_results[-1]["href"]
            soup = set_soup(results_url)
            table = soup.find("table", {"class": "resultsarchive-table"})
            if table is None:
                logger.info(f"Results table not found for year {self.date.year}")
                return
            rows = table.find_all("tr")[1 : amount + 1]
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
            logger.exception(f"Error getting race results for year {self.date.year}")

    def get_driver_standings(self, amount=5):
        """
        Gets top drivers from overall standings and url for more details
        """
        url = f"{self.BASE_URL}/en/results.html/{self.date.year}/drivers.html"
        try:
            soup = set_soup(url)
            table = soup.find("table", {"class": "resultsarchive-table"})
            if table is None:
                logger.info(
                    f"Driver standings table not found for year {self.date.year}"
                )
                return
            rows = table.find_all("tr")[1 : amount + 1]
            driver_rows = [
                [cell.text.strip() for cell in row.find_all("td")] for row in rows
            ]
            standings = [
                {
                    "driver": row[2],
                    "position": int(row[1]),
                    "points": float(row[-2]),
                }
                for row in driver_rows
            ]
            return {"driverStandings": standings, "driverUrl": url}
        except Exception:
            logger.exception(
                f"Error getting driver standings for year {self.date.year}"
            )

    def get_team_standings(self, amount=5):
        """
        Gets top teams from overall standings and url for more details
        """
        url = f"{self.BASE_URL}/en/results.html/{self.date.year}/team.html"
        try:
            soup = set_soup(url)
            table = soup.find("table", {"class": "resultsarchive-table"})
            if table is None:
                logger.info(f"Team standings table not found for year {self.date.year}")
                return
            rows = table.find_all("tr")[1 : amount + 1]
            team_rows = [
                [cell.text.strip() for cell in row.find_all("td")] for row in rows
            ]
            standings = [
                {
                    "team": row[2],
                    "position": int(row[1]),
                    "points": float(row[-2]),
                }
                for row in team_rows
            ]
            return {"teamStandings": standings, "teamUrl": url}
        except Exception:
            logger.exception(f"Error getting team standings {self.date.year}")

    def get_upcoming(self):
        """
        Gets info for the upcoming race
        """
        try:
            race = next(
                (
                    race
                    for race in self.race_weekends
                    if race["sessions"]["race"] >= self.date
                ),
                self.race_weekends[-1],
            )
            return race
        except Exception:
            logger.exception(f"Error getting upcoming race for year {self.date.year}")

    def find_circuit_image(self, url):
        """
        Gets image for race circuit
        """
        try:
            soup = set_soup(url)
            img_url_container = soup.find(
                "div", {"class": "f1-race-hub--schedule-circuit-map"}
            )
            img_url = img_url_container.find("a")["href"]
            soup = set_soup(self.BASE_URL + img_url)
            img_container = soup.find("div", {"class": "f1-race-hub--map-container"})
            img = img_container.find("img", {"class": "lazy"})["data-src"]
            return self._add_timestamp_to_image(img)
        except Exception:
            logger.exception("Error getting circuit image")

    def _add_timestamp_to_image(self, img):
        if isinstance(img, str):
            return f"{img}?a={datetime.utcnow().isoformat()}"
        return img