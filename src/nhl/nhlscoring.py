import json
from src.common.utils import format_as_code, format_as_header, format_as_url, get
from .nhlbase import NHLBase
from ..common.logger import logging

logger = logging.getLogger(__name__)


class NHLScoring(NHLBase):
    def __init__(self):
        super().__init__()
        self.api_base_url = "https://api.nhle.com/stats/rest/en"
        self.details_url = "https://www.nhl.com/stats/skaters"

    def get_scoring_leaders(self, amount=10, filter=None):
        url = f"{self.api_base_url}/skater/summary"
        sort = [
            {"property": "points", "direction": "DESC"},
            {"property": "goals", "direction": "DESC"},
            {"property": "assists", "direction": "DESC"},
            {"property": "playerId", "direction": "ASC"},
        ]
        exp = (
            f"""gameTypeId=2 and seasonId<={self.season} and seasonId>={self.season}"""
        )
        if filter is not None:
            franchises = self._get_franchises()
            if filter.upper() in franchises:
                exp += f"""and franchiseId=\"{franchises[filter.upper()]}\""""
            else:
                exp += f"""and nationalityCode=\"{filter.upper()}\""""
        params = {
            "isAggregate": "false",
            "isGame": "false",
            "sort": json.dumps(sort),
            "start": 0,
            "limit": 100,
            "factCayenneExp": "gamesPlayed>=1",
            "cayenneExp": exp,
        }
        try:
            res = get(url, params).json()
            if not res["data"]:
                logger.info(
                    f"No scoring info found for season {self.season} with filter {filter}"
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
                f"Error getting scoring leaders for season {self.season} with filter {filter}"
            )

    def format(self, data):
        highest_points = max(data, key=lambda x: x["points"])
        highest_points_len = len(str(highest_points["points"]))
        highest_goals = max(data, key=lambda x: x["goals"])
        highest_goals_len = len(str(highest_goals["goals"]))
        highest_assists = max(data, key=lambda x: x["assists"])
        highest_assists_len = len(str(highest_assists["assists"]))

        adjust = highest_goals_len + highest_assists_len + 1

        leaders = [
            (
                f"""{str(player["rank"]).rjust(2)}. """
                + f"""{(str(player["goals"]) + "+" + str(player["assists"])).rjust(adjust)}"""
                + f"""={str(player["points"]).ljust(highest_points_len)} """
                + f"""{player["name"].split(" ")[-1]} ({player["team"]})"""
            )
            for player in data
        ]
        text = (
            format_as_header("Scoring leaders:")
            + "\n"
            + format_as_code("\n".join(leaders))
            + format_as_url(self.details_url)
        )
        return text

    def _get_franchises(self):
        url = f"{self.api_base_url}/franchise"
        res = get(url).json()
        franchises = {}
        for team in res["data"]:
            for key, value in self.teams.items():
                if value == team["fullName"]:
                    franchises[key] = team["id"]
        return franchises
