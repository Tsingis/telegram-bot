import pandas as pd
from .nhlbase import NHLBase
from ..common import set_soup
from ...logger import logging


logger = logging.getLogger(__name__)


class NHLExtra(NHLBase):
    def __init__(self):
        super().__init__()

    # Get player contract info for current season
    def get_player_contract(self, name):
        name = name.replace(" ", "-").replace("\'", "").lower()
        url = f"https://www.capfriendly.com/players/{name}"
        try:
            soup = set_soup(url, targetEncoding="utf-8")

            # Find table of current contract
            table = soup.find("table", {"class": "cntrct fixed tbl"})

            # Put data into dataframe
            data = pd.read_html(table.prettify(), flavor="bs4", header=0)[0]

            # Alter season column format
            data["SEASON"] = data["SEASON"].apply(
                lambda x: x.replace("-", "20"))

            # Filter for current season
            seasonMask = data["SEASON"] == self.season

            # Get length, cap hit and total salary of current contract
            contract = {
                "length": f"{data.index[seasonMask].values[0] + 1}/{len(data) - 1}",
                "capHit": data["CAP HIT"][seasonMask].values[0],
                "totalSalary": data["TOTAL SALARY"][seasonMask].values[0],
            }
            return {
                "contract": contract,
                "url": url
            }
        except Exception:
            logger.exception(
                f"Error getting player contract for player: {name}")

    def format_player_contract(self, data):
        header = "Contract:\n"
        contract = (f"""Year: {data["contract"]["length"]} | """ +
                    f"""Cap hit: {data["contract"]["capHit"]} | """ +
                    f"""Total: {data["contract"]["totalSalary"]}""")
        return header + contract + f"""\n[Details]({data["url"]})"""
