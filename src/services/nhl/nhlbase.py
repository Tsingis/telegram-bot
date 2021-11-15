from datetime import datetime
from ..common import convert_timezone, get
from ...logger import logging


logger = logging.getLogger(__name__)


class NHLBase:
    BASE_URL = "https://statsapi.web.nhl.com/api/v1"

    def __init__(self, date=datetime.utcnow()):
        self.targetTimezone = "Europe/Helsinki"
        self.date = convert_timezone(date=date, target_tz=self.targetTimezone)
        year = self.date.year
        self.season = f"{year-1}{year}" if self.date.month < 9 else f"{year}{year+1}"

    def get_player(self, player_id):
        try:
            url = f"{self.BASE_URL}/people/{player_id}"
            data = get(url).json()
            player = {
                "id": player_id,
                "name": data["people"][0]["fullName"],
                "team": data["people"][0]["currentTeam"]["name"],
                "position": data["people"][0]["primaryPosition"]["name"],
                "number": data["people"][0]["primaryNumber"],
            }
            return player
        except Exception:
            logger.exception(f"Error getting player with id: {player_id}")

    def get_player_season_stats(self, player_id):
        try:
            url = f"{self.BASE_URL}/people/{player_id}/stats?stats=statsSingleSeason&season={self.season}"
            data = get(url).json()
            stats = data["stats"][0]["splits"][0]["stat"]
            return stats
        except Exception:
            logger.exception(f"Error getting player stats with id: {player_id}")

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

    def get_games(self, date):
        try:
            url = f"{self.BASE_URL}/schedule?date={date}"
            data = get(url).json()
            games = [
                {
                    "id": game["gamePk"],
                    "homeTeam": game["teams"]["home"]["team"]["name"],
                    "awayTeam": game["teams"]["away"]["team"]["name"],
                    "date": game["gameDate"],
                    "status": game["status"]["detailedState"],
                }
                for game in data["dates"][0]["games"]
            ]
            return games
        except Exception:
            logger.exception(f"Error getting games for date: {date}")

    def get_games_linescore(self, game_id):
        try:
            url = f"{self.BASE_URL}/game/{game_id}/linescore"
            data = get(url).json()
            return data
        except Exception:
            logger.exception(f"Error getting games linescore with game id: {game_id}")

    def get_games_boxscore(self, game_id):
        try:
            url = f"{self.BASE_URL}/game/{game_id}/boxscore"
            data = get(url).json()
            return data
        except Exception:
            logger.exception(f"Error getting games boxscore with game id: {game_id}")

    def get_roster(self, teamId):
        try:
            url = f"{self.BASE_URL}/teams/{teamId}/roster"
            data = get(url).json()
            roster = [
                {"id": player["person"]["id"], "name": player["person"]["fullName"]}
                for player in data["roster"]
            ]
            return roster
        except Exception:
            logger.exception(f"Error getting rosters with team id: {teamId}")

    def get_division_leaders(self, date, amount=3):
        try:
            url = f"{self.BASE_URL}/standings/byDivision?date={date}"
            teams = self.get_teams()
            data = get(url).json()
            # Get divisions
            divs = [
                {
                    "conference": div["conference"]["name"],
                    "division": div["division"]["name"],
                    "data": div["teamRecords"],
                }
                for div in data["records"]
            ]
            # Get top three leaders on default from each division
            leaders = [
                {
                    "conference": div["conference"],
                    "division": div["division"],
                    "teams": [
                        {
                            "name": teams[team["team"]["name"]]["shortName"],
                            "points": team["points"],
                            "games": team["gamesPlayed"],
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
            url = f"{self.BASE_URL}/standings/wildCard?date={date}"
            teams = self.get_teams()
            data = get(url).json()
            # Get top five wildcards on default from each conference
            wilds = [
                {
                    "conference": conf["conference"]["name"],
                    "teams": [
                        {
                            "name": teams[wild["team"]["name"]]["shortName"],
                            "points": wild["points"],
                            "games": wild["gamesPlayed"],
                        }
                        for wild in conf["teamRecords"][:amount]
                    ],
                }
                for conf in data["records"]
            ]
            return wilds
        except Exception:
            logger.exception(f"Error getting wildcards for date {date}")

    def get_playoffs(self):
        try:
            url = f"{self.BASE_URL}/tournaments/playoffs?expand=round.series,schedule.seriesSummary&season={self.season}"
            playoffs = get(url).json()
            return playoffs
        except Exception:
            logger.exception(f"Error getting playoffs for season {self.season}")
