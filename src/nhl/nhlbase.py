from datetime import datetime
from ..common.utils import get, convert_timezone, datetime_to_text
from ..common.logger import logging


logger = logging.getLogger(__name__)


class NHLBase:
    BASE_URL = "https://statsapi.web.nhl.com/api/v1"

    def __init__(self, date=datetime.utcnow()):
        self.date_format = "%Y-%m-%d"
        self.timezone = "Europe/Helsinki"
        self.date = convert_timezone(date=date, target_tz=self.timezone)
        year = self.date.year
        self.season = f"{year-1}{year}" if self.date.month < 9 else f"{year}{year+1}"
        self.teams = self.get_teams()

    def get_player(self, player_id):
        try:
            url = f"{self.BASE_URL}/people/{player_id}"
            res = get(url).json()
            info = res["people"][0]
            player = {
                "id": player_id,
                "name": info["fullName"],
                "team": info["currentTeam"]["name"],
                "age": info["currentAge"],
                "nationality": info["nationality"],
                "position": info["primaryPosition"]["abbreviation"],
                "number": info["primaryNumber"],
            }
            return player
        except Exception:
            logger.exception(f"Error getting player id {player_id}")

    def get_player_season_stats(self, player_id):
        try:
            url = f"{self.BASE_URL}/people/{player_id}/stats?stats=statsSingleSeason&season={self.season}"
            res = get(url).json()
            if not res["stats"][0]["splits"]:
                logger.info(f"No season stats found for player id {player_id}")
                return
            stats = res["stats"][0]["splits"][0]["stat"]
            return stats
        except Exception:
            logger.exception(f"Error getting season stats for player id {player_id}")

    def get_games(self, date):
        try:
            date = datetime_to_text(date, self.date_format)
            url = f"{self.BASE_URL}/schedule?date={date}"
            res = get(url).json()
            if not res["dates"]:
                return
            games = [
                {
                    "id": game["gamePk"],
                    "homeTeam": game["teams"]["home"]["team"]["name"],
                    "awayTeam": game["teams"]["away"]["team"]["name"],
                    "date": game["gameDate"],
                    "status": game["status"]["detailedState"],
                }
                for game in res["dates"][0]["games"]
            ]
            return games
        except Exception:
            logger.exception(f"Error getting games for date {date}")

    def get_games_linescore(self, game_id):
        try:
            url = f"{self.BASE_URL}/game/{game_id}/linescore"
            res = get(url).json()
            return res
        except Exception:
            logger.exception(f"Error getting games linescore with game id {game_id}")

    def get_games_boxscore(self, game_id):
        try:
            url = f"{self.BASE_URL}/game/{game_id}/boxscore"
            res = get(url).json()
            return res
        except Exception:
            logger.exception(f"Error getting games boxscore with game id {game_id}")

    def get_roster(self, team_id):
        try:
            url = f"{self.BASE_URL}/teams/{team_id}/roster"
            res = get(url).json()
            roster = [
                {"id": player["person"]["id"], "name": player["person"]["fullName"]}
                for player in res["roster"]
            ]
            return roster
        except Exception:
            logger.exception(f"Error getting rosters with team id {team_id}")

    def get_division_leaders(self, date, amount=3):
        try:
            date = datetime_to_text(date, self.date_format)
            url = f"{self.BASE_URL}/standings/byDivision?date={date}"
            res = get(url).json()
            divs = [
                {
                    "conference": div["conference"]["name"],
                    "division": div["division"]["name"],
                    "data": div["teamRecords"],
                }
                for div in res["records"]
            ]
            leaders = [
                {
                    "conference": div["conference"],
                    "division": div["division"],
                    "teams": [
                        {
                            "name": self.get_team_shortname(team["team"]["name"]),
                            "points": team["points"],
                            "games": team["gamesPlayed"],
                            "record": team["leagueRecord"],
                            "streak": team["streak"]["streakCode"]
                            if "streak" in team
                            else None,
                        }
                        for team in div["data"][:amount]
                    ],
                }
                for div in divs
            ]
            return leaders
        except Exception:
            logger.exception(f"Error getting division leaders for date {date}")

    def get_wildcards(self, date, amount=5):
        try:
            date = datetime_to_text(date, self.date_format)
            url = f"{self.BASE_URL}/standings/wildCard?date={date}"
            res = get(url).json()
            wilds = [
                {
                    "conference": conf["conference"]["name"],
                    "teams": [
                        {
                            "name": self.get_team_shortname(team["team"]["name"]),
                            "points": team["points"],
                            "games": team["gamesPlayed"],
                            "record": team["leagueRecord"],
                            "streak": team["streak"]["streakCode"]
                            if "streak" in team
                            else None,
                        }
                        for team in conf["teamRecords"][:amount]
                    ],
                }
                for conf in res["records"]
            ]
            return wilds
        except Exception:
            logger.exception(f"Error getting wildcards for date {date}")

    def get_playoffs(self):
        try:
            url = f"{self.BASE_URL}/tournaments/playoffs?expand=round.series,schedule.seriesSummary&season={self.season}"
            res = get(url).json()
            return res
        except Exception:
            logger.exception(f"Error getting playoffs for season {self.season}")

    def get_teams(self):
        try:
            url = f"{self.BASE_URL}/teams"
            data = get(url).json()
            teams = {
                team["name"]: {"id": team["id"], "shortName": team["abbreviation"]}
                for team in data["teams"]
                if team["active"] and "firstYearOfPlay" in team
            }
            return teams
        except Exception:
            logger.exception("Error getting teams")

    def get_team_shortname(self, name):
        if name in self.teams:
            return self.teams[name]["shortName"]
        return name