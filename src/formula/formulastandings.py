import re
from .formulabase import FormulaBase
from ..common.logger import logging
from ..common.utils import (
    format_as_monospace,
    format_as_header,
    format_as_url,
    format_number,
    set_selector,
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
            selector = set_selector(url, "utf8")
            table = selector.xpath("//div[@id='results-table']//table")

            if not table:
                logger.info(f"Driver standings table not found for year {self.date.year}")
                return

            rows = table.xpath(".//tr[position() > 1]")  # exclude header
            standings = []
            for row in rows:
                cells = [td.xpath("string()").get().strip() for td in row.xpath(".//td")]

                if len(cells) < 3:
                    continue

                standings.append(
                    {
                        "driver": cells[1],
                        "position": cells[0],
                        "points": float(cells[-1]),
                    }
                )
            amount = max(len(standings), amount)
            return {
                "driverStandings": standings[:amount],
                "driverUrl": url,
            }
        except Exception:
            logger.exception(f"Error getting driver standings for year {self.date.year}")

    def get_team_standings(self, amount=5):
        """
        Gets top teams from overall standings and url for more details
        """
        url = f"{self.base_url}/en/results/{self.date.year}/team"
        try:
            selector = set_selector(url, "utf8")
            table = selector.xpath("//div[@id='results-table']//table")

            if not table:
                logger.info(f"Team standings table not found for year {self.date.year}")
                return

            rows = table.xpath(".//tr[position() > 1]")  # exclude header
            standings = []
            for row in rows:
                cells = row.xpath(".//td/text()").getall()
                cells = [td.xpath("string()").get().strip() for td in row.xpath(".//td")]

                if len(cells) < 3:
                    continue

                standings.append(
                    {
                        "team": cells[1],
                        "position": cells[0],
                        "points": float(cells[-1]),
                    }
                )
            amount = max(len(standings), amount)
            return {
                "teamStandings": standings[:amount],
                "teamUrl": url,
            }
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
