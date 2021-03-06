import requests
from datetime import datetime
from .common import convert_timezone
from ..logger import logging


logger = logging.getLogger(__name__)


class NHLBase:
    BASE_URL = "https://statsapi.web.nhl.com/api/v1"

    def __init__(self, date=datetime.utcnow()):
        self.targetTimezone = "Europe/Helsinki"
        self.date = convert_timezone(date=date, targetTz=self.targetTimezone)
        year = self.date.year
        self.season = f"{year-1}{year}" if self.date.month < 9 else f"{year}{year+1}"

    # Get player basic info
    def get_player(self, playerId):
        try:
            data = self._get_data(f"{self.BASE_URL}/people/{playerId}")
            player = {
                "id": playerId,
                "name": data["people"][0]["fullName"],
                "team": data["people"][0]["currentTeam"]["name"],
                "position": data["people"][0]["primaryPosition"]["name"],
                "number": data["people"][0]["primaryNumber"]
            }
            return player
        except Exception:
            logger.exception(f"Error getting player with id: {playerId}")

    # Get player's regular season stats
    def get_player_season_stats(self, playerId):
        try:
            data = self._get_data(
                f"{self.BASE_URL}/people/{playerId}/stats?stats=statsSingleSeason&season={self.season}")
            stats = data["stats"][0]["splits"][0]["stat"]
            return stats
        except Exception:
            logger.exception(f"Error getting player stats with id: {playerId}")

    # Get teams with ids and abbreviations
    def get_teams(self):
        try:
            data = self._get_data(f"{self.BASE_URL}/teams")
            teams = {
                team["name"]: {"id": team["id"], "shortName": team["abbreviation"]} for team in data["teams"]
                if team["active"] and "firstYearOfPlay" in team}
            return teams
        except Exception:
            logger.exception("Error getting teams")

    # Get game info for each match on given date
    def get_games(self, date):
        try:
            data = self._get_data(f"{self.BASE_URL}/schedule?date={date}")
            games = [
                {
                    "id": game["gamePk"],
                    "homeTeam": game["teams"]["home"]["team"]["name"],
                    "awayTeam": game["teams"]["away"]["team"]["name"],
                    "date": game["gameDate"],
                    "status": game["status"]["detailedState"],
                } for game in data["dates"][0]["games"]]
            return games
        except Exception:
            logger.exception(f"Error getting games for date: {date}")

    # Get data from each match by gameId
    def get_games_linescore(self, gameId):
        try:
            data = self._get_data(f"{self.BASE_URL}/game/{gameId}/linescore")
            return data
        except Exception:
            logger.exception(
                f"Error getting games linescore with game id: {gameId}")

    # Get data from each match by gameId
    def get_games_boxscore(self, gameId):
        try:
            data = self._get_data(f"{self.BASE_URL}/game/{gameId}/boxscore")
            return data
        except Exception:
            logger.exception(
                f"Error getting games boxscore with game id: {gameId}")

    # Get rosters with teamId
    def get_roster(self, teamId):
        try:
            data = self._get_data(f"{self.BASE_URL}/teams/{teamId}/roster")
            roster = [{
                "id": player["person"]["id"],
                "name": player["person"]["fullName"]
            } for player in data["roster"]]
            return roster
        except Exception:
            logger.exception(f"Error getting rosters with team id: {teamId}")

    # Get division leaders
    def get_division_leaders(self, date, amount=3):
        try:
            teams = self.get_teams()
            data = self._get_data(
                f"{self.BASE_URL}/standings/byDivision?date={date}")
            # Get divisions
            divs = [
                {
                    "conference": div["conference"]["name"],
                    "division": div["division"]["name"],
                    "data": div["teamRecords"]
                }
                for div in data["records"]
            ]
            # Get top three leaders on default from each division
            leaders = [{
                "conference": div["conference"],
                "division": div["division"],
                "teams": [
                    {
                        "name": teams[team["team"]["name"]]["shortName"],
                        "points": str(team["points"]),
                        "games": str(team["gamesPlayed"])
                    }
                    for team in div["data"][:amount]
                ]}
                for div in divs]
            return leaders
        except Exception:
            logger.exception(
                f"Error getting division leaders for date {date}")

    # Get wildcards
    def get_wildcards(self, date, amount=5):
        try:
            teams = self.get_teams()
            data = self._get_data(
                f"{self.BASE_URL}/standings/wildCard?date={date}")
            # Get top five wildcards on default from each conference
            wilds = [{
                "conference": conf["conference"]["name"],
                "teams": [
                    {
                        "name": teams[wild["team"]["name"]]["shortName"],
                        "points": str(wild["points"]),
                        "games": str(wild["gamesPlayed"])
                    }
                    for wild in conf["teamRecords"][:amount]
                ]}
                for conf in data["records"]]
            return wilds
        except Exception:
            logger.exception(f"Error getting wildcards for date {date}")

    # Get playoffs info
    def get_playoffs(self):
        try:
            playoffs = self._get_data(
                f"{self.BASE_URL}/tournaments/playoffs?expand=round.series,schedule.seriesSummary&season={self.season}")
            return playoffs
        except Exception:
            logger.exception(
                f"Error getting playoffs for season {self.season}")

    # Get JSON formatted data from given url
    def _get_data(self, url):
        try:
            res = requests.get(url)
            if (res.status_code == 200):
                return res.json()
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            logger.exception(f"Error getting data with url: {url}")
