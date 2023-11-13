from .nhlbase import NHLBase
from ..common.utils import (
    escape_special_chars,
    format_as_header,
    format_as_url,
    set_soup,
)
from ..common.logger import logging

logger = logging.getLogger(__name__)


class NHLContract(NHLBase):
    def __init__(self):
        super().__init__()
        self.contract_base_url = "https://www.capfriendly.com/players"

    def get(self, name):
        url = f"""{self.contract_base_url}/{name.replace(" ", "-").replace("'", "").lower()}"""
        try:
            soup = set_soup(url, target_encoding="utf-8")
            table = soup.find_all("table")[0]
            if table is None:
                logger.info(f"Contract table not found for player {name}")
                return
            rows = table.find_all("tr")
            contract_rows = [
                row.find_all("td") for row in rows[1:-1]
            ]  # Skip header and total rows
            data = [
                {
                    "season": cols[0].text.replace("-", "20"),
                    "capHit": cols[2].text,
                    "totalSalary": cols[7].text,
                }
                for cols in contract_rows
            ]
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
            logger.exception(f"Error getting player contract for player {name}")

    def format(self, player_name, data):
        contract = {
            "year": data["contract"]["yearStatus"],
            "cap": data["contract"]["capHit"],
        }
        contract_text = "\n".join(
            [f"{key.capitalize()}: {value}" for (key, value) in contract.items()]
        )
        text = (
            format_as_header(f"Contract of {player_name.title()}")
            + "\n"
            + escape_special_chars(contract_text)
            + "\n"
            + format_as_url(data["url"])
        )
        return text
