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
            table = soup.find("table", {"class": "cntrct fixed"})
            rows = table.find_all("tr")[1:-1]  # Skip header and total rows
            contract_rows = [row.find_all("td") for row in rows]
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
            logger.exception(f"Error getting player contract for player: {name}")

    def format_player_contract(self, data):
        header = "Contract:\n"
        contract = (
            f"""Year: {data["contract"]["yearStatus"]} | """
            + f"""Cap hit: {data["contract"]["capHit"]} | """
            + f"""Total: {data["contract"]["totalSalary"]}"""
        )
        return header + contract + f"""\n[Details]({data["url"]})"""

    def get_scoring_leaders(self, amount=10):
        try:
            season = f"{self.season[:4]}-{self.season[-2:]}"
            url = f"https://www.quanthockey.com/nhl/seasons/{season}-nhl-players-stats.html"
            soup = set_soup(url)
            table = soup.find("table", {"id": "statistics"})
            body_rows = [row for row in table.find("tbody").find_all("tr")][:amount]
            stats = [[stats.text for stats in row.find_all("td")] for row in body_rows]
            data = [
                {
                    "rank": idx + 1,
                    "name": row.find_all("th")[2].text,
                    "team": stats[idx][0],
                    "gamesPlayed": int(stats[idx][3]),
                    "goals": int(stats[idx][4]),
                    "assists": int(stats[idx][5]),
                    "points": int(stats[idx][6]),
                }
                for idx, row in enumerate(body_rows)
            ]
            return data
        except Exception:
            logger.exception("Error getting scoring leaders")

    def format_scoring_leaders(self, data):
        leaders = [
            (
                f"""{player["rank"]}. {player["name"].split(" ")[-1]} ({player["team"]})"""
                + f""" | {player["goals"]}+{player["assists"]}={player["points"]}"""
            )
            for player in data
        ]
        return "\n".join(leaders)
