import re
from .formulabase import FormulaBase
from ..common.logger import logging
from ..common.utils import (
    format_as_monospace,
    format_as_header,
    format_as_url,
    format_number,
    set_soup,
)


logger = logging.getLogger(__name__)


class FormulaStandings(FormulaBase):
    def __init__(self):
        super().__init__()

    def get_driver_standings(self, amount=5):
        """
        Gets top drivers from overall standings and url for more details
        """
        url = f"{self.base_url}/en/results/{self.date.year}/drivers"
        try:
            soup = set_soup(url, "utf8")
            table = soup.find("table", {"class": ["f1-table"]})
            if table is None:
                logger.info(f"Driver standings table not found for year {self.date.year}")
                return
            rows = table.find_all("tr")[1:]  # Exclude header
            driver_rows = [[cell.text.strip() for cell in row.find_all("td")] for row in rows]
            standings = [
                {
                    "driver": row[1],
                    "position": row[0],
                    "points": float(row[-1]),
                }
                for row in driver_rows
            ]
            return {"driverStandings": standings[:amount], "driverUrl": url}
        except Exception:
            logger.exception(f"Error getting driver standings for year {self.date.year}")

    def get_team_standings(self, amount=5):
        """
        Gets top teams from overall standings and url for more details
        """
        url = f"{self.base_url}/en/results/{self.date.year}/team"
        try:
            soup = set_soup(url, "utf8")
            table = soup.find("table", {"class": ["f1-table"]})
            if table is None:
                logger.info(f"Team standings table not found for year {self.date.year}")
                return
            rows = table.find_all("tr")[1:]  # Exclude header and notes
            team_rows = [[cell.text.strip() for cell in row.find_all("td")] for row in rows]
            standings = [
                {
                    "team": row[1],
                    "position": row[0],
                    "points": float(row[-1]),
                }
                for row in team_rows
            ]
            return {"teamStandings": standings[:amount], "teamUrl": url}
        except Exception:
            logger.exception(f"Error getting team standings {self.date.year}")

    def format(self, data):
        for standing in data["teamStandings"]:
            team_name_parts = standing["team"].split(" ")
            if len(team_name_parts) <= 2:
                team = standing["team"]
            else:
                team_name_parts_inner = re.sub(r"([A-Z])", r" \1", standing["team"]).split()
                team = " ".join(team_name_parts_inner[:2])
            standing["team"] = team

        driver_standings = [
            f"""{str(result["position"]).rjust(2)}. {result["driver"][-3:]} - {format_number(result["points"])}"""
            for result in data["driverStandings"]
        ]

        longest_team_name = max([len(result["team"]) for result in data["teamStandings"]])
        team_standings = [
            f"""{str(result["position"]).rjust(2)}. {result["team"].ljust(longest_team_name)} - {format_number(result["points"])}"""
            for result in data["teamStandings"]
        ]

        header = "Standings:"
        text = (
            format_as_header(header)
            + "\n"
            + format_as_header("Drivers:")
            + "\n"
            + format_as_monospace("\n".join(driver_standings))
            + "\n"
            + format_as_url(data["driverUrl"])
            + "\n\n"
            + format_as_header("Teams:")
            + "\n"
            + format_as_monospace("\n".join(team_standings))
            + "\n"
            + format_as_url(data["teamUrl"])
        )
        return text
