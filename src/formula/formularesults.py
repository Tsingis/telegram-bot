from .formulabase import FormulaBase
from ..common.logger import logging
from ..common.utils import (
    format_as_monospace,
    format_as_header,
    format_as_url,
    set_selector,
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
            selector = set_selector(url, "utf8")
            races_table = selector.xpath("//div[@id='results-table']//table")

            if not races_table:
                logger.info(f"Races table not found for year {self.date.year}")
                return

            race_links = races_table.xpath(".//a[@href]/@href").getall()

            if not race_links:
                logger.info(f"No past races found for year {self.date.year}")
                return

            results_url = self.base_url + race_links[-1]
            selector = set_selector(results_url, "utf8")

            table = selector.xpath("//div[@id='results-table']//table")

            if not table:
                logger.info(f"Results table not found for year {self.date.year}")
                return

            rows = table.xpath(".//tr[position() > 1 and position() < last()]")
            results = []
            for row in rows:
                cells = [td.xpath("string()").get().strip() for td in row.xpath(".//td")]

                if len(cells) < 4:
                    continue

                results.append(
                    {
                        "name": cells[2],
                        "position": cells[0],
                        "time": cells[-2],
                    }
                )
            return {
                "results": results[:amount],
                "url": results_url,
            }

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
