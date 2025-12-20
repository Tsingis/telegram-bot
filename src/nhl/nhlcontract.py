from .nhlbase import NHLBase
from ..common.utils import (
    escape_special_chars,
    format_as_header,
    format_as_url,
    set_selector,
)
from ..common.logger import logging

logger = logging.getLogger(__name__)


class NHLContract(NHLBase):
    def __init__(self):
        super().__init__()
        self.contract_base_url = "https://capwages.com/players"

    def get(self, name):
        url = f"""{self.contract_base_url}/{name.replace(" ", "-").replace("'", "").lower()}"""
        try:
            selector = set_selector(url, target_encoding="utf-8")

            tables = selector.xpath(
                "//table[contains(@class, 'min-w-full') " "and contains(@class, 'bg-white')]"
            )

            if not tables:
                logger.info(f"Contract table not found for player {name}")
                return

            for table in tables:
                rows = table.xpath(".//tr")[1:-1]  # skip header & total rows

                data = []
                for row in rows:
                    cols = row.xpath(".//td")
                    if len(cols) < 3:
                        continue

                    season = cols[0].xpath("string()").get().replace("-", "20")
                    cap_hit = cols[2].xpath("string()").get()

                    data.append(
                        {
                            "season": season,
                            "capHit": cap_hit,
                        }
                    )

                contract = next(
                    (
                        {
                            "yearStatus": f"{i + 1}/{len(data)}",
                            "capHit": item["capHit"],
                        }
                        for i, item in enumerate(data)
                        if item["season"] == self.season
                    ),
                    None,
                )

                if contract:
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
