from .formulabase import FormulaBase
from ..common.logger import logging
from ..common.utils import (
    format_as_monospace,
    format_as_header,
    format_as_url,
    set_soup,
)


logger = logging.getLogger(__name__)


class FormulaResults(FormulaBase):
    def __init__(self):
        super().__init__()

    def get_results(self, amount=10):
        """
        Gets top drivers from the latest race and url for more details
        """
        url = f"{self.base_url}/en/results/{self.date.year}/races"
        try:
            soup = set_soup(url, "utf8")
            races_table = soup.find("table", {"class": ["f1-table"]})
            if races_table is None:
                logger.info(f"Races table not found for year {self.date.year}")
                return
            race_results = races_table.find_all("a")
            if not race_results:
                logger.info(f"No past races found for year {self.date.year}")
                return
            results_url = url.replace("races", "") + race_results[-1]["href"]
            soup = set_soup(results_url, "utf8")
            table = soup.find("table", {"class": ["f1-table"]})
            if table is None:
                logger.info(f"Results table not found for year {self.date.year}")
                return
            rows = table.find_all("tr")[1:-1]  # Exclude both header and notes
            driver_rows = [[cell.text.strip() for cell in row.find_all("td")] for row in rows]
            results = [
                {
                    "name": row[2],
                    "position": row[0],
                    "time": row[-2],
                }
                for row in driver_rows
            ]
            return {"results": results[:amount], "url": results_url}
        except Exception:
            logger.exception(f"Error getting race results for year {self.date.year}")

    def format(self, data):
        url = data["url"]
        race = url.split("/")[-2].replace("-", " ").title()
        formatted_results = [
            f"""{str(result["position"]).rjust(2)}. {result["name"][-3:]} {result["time"]}"""
            for result in data["results"]
        ]

        header = f"Results for {race}:"
        text = (
            format_as_header(header)
            + "\n"
            + format_as_monospace("\n".join(formatted_results))
            + "\n"
            + format_as_url(url)
        )
        return text
