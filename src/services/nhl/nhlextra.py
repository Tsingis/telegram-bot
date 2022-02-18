from .nhlbase import NHLBase
from ..utils import set_soup, get
from ...logger import logging
from re import compile
from json import dumps

logger = logging.getLogger(__name__)


class NHLExtra(NHLBase):
    def __init__(self):
        super().__init__()

    def get_player_contract(self, name):
        """
        Player contract info for current season from Capfriendly
        """
        name = name.replace(" ", "-").replace("'", "").lower()
        url = f"https://www.capfriendly.com/players/{name}"
        try:
            soup = set_soup(url, target_encoding="utf-8")
            table = soup.find(
                "table",
                {"class": compile("^cntrct fixed")},
            )
            if table is None:
                logger.warning(f"Contract table not found for player {name}")
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

    def get_scoring_leaders(self, amount=10, nationality=None):
        """
        Scoring leaders for current season from NHL
        """
        url = "https://api.nhle.com/stats/rest/en/skater/summary"
        sort = [
            {"property": "points", "direction": "DESC"},
            {"property": "goals", "direction": "DESC"},
            {"property": "assists", "direction": "DESC"},
            {"property": "playerId", "direction": "ASC"},
        ]
        exp = (
            f"""gameTypeId=2 and seasonId<={self.season} and seasonId>={self.season}"""
        )
        if nationality is not None:
            exp += f"""and nationalityCode=\"{nationality.upper()}\""""
        params = {
            "isAggregate": "false",
            "isGame": "false",
            "sort": dumps(sort),
            "start": 0,
            "limit": 100,
            "factCayenneExp": "gamesPlayed>=1",
            "cayenneExp": exp,
        }
        try:
            res = get(url, params).json()
            if not res["data"]:
                logger.warning(
                    f"No scoring info found for season {self.season} with nationatality {nationality}"
                )
                return
            data = [
                {
                    "rank": idx + 1,
                    "name": player["lastName"],
                    "team": player["teamAbbrevs"],
                    "gamesPlayed": player["gamesPlayed"],
                    "goals": player["goals"],
                    "assists": player["assists"],
                    "points": player["points"],
                }
                for idx, player in enumerate(res["data"][:amount])
            ]
            return data
        except Exception:
            logger.exception(
                f"Error getting scoring leaders for season {self.season} with nationality {nationality}"
            )
