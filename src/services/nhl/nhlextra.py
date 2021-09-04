from .nhlbase import NHLBase
from ..common import set_soup
from ...logger import logging


logger = logging.getLogger(__name__)


class NHLExtra(NHLBase):
    def __init__(self):
        super().__init__()

    # Get player contract info for current season
    def get_player_contract(self, name):
        name = name.replace(" ", "-").replace("'", "").lower()
        url = f"https://www.capfriendly.com/players/{name}"
        try:
            soup = set_soup(url, target_encoding="utf-8")
            table = soup.find("table", {"class": "cntrct fixed tbl"})

            data = []
            rows = table.find_all("tr")[1:-1]  # Skip header and total rows
            for row in rows:
                cells = row.find_all("td")
                data.append(
                    {
                        "season": cells[0].text.replace("-", "20"),
                        "capHit": cells[2].text,
                        "totalSalary": cells[7].text,
                    }
                )

            contract = next(
                {
                    "yearStatus": f"{i+1}/{len(data)}",
                    "capHit": item["capHit"],
                    "totalSalary": item["totalSalary"],
                }
                for i, item in enumerate(data)
                if item["season"] == self.season
            )

            return {"contract": contract, "url": url}
        except Exception:
            logger.exception(f"Error getting player contract for player: {name}")

    def format_player_contract(self, data):
        header = "Contract:\n"
        contract = (
            f"""Year: {data["contract"]["yearStatus"]} | """
            + f"""Cap hit: {data["contract"]["capHit"]} | """
            + f"""Total: {data["contract"]["totalSalary"]}"""
        )
        return header + contract + f"""\n[Details]({data["url"]})"""
