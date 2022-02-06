from datetime import timedelta
from .nhlbase import NHLBase
from ...logger import logging


logger = logging.getLogger(__name__)


class NHLAdvanced(NHLBase):
    def __init__(self):
        super().__init__()

    def get_results(self):
        """
        Match results from the latest round
        """
        date = self.date - timedelta(days=1)
        try:
            games = self.get_games(date)
            if games is None:
                logger.warning(f"No games found for date {date}")
                return
            games = [
                self.get_games_linescore(game["id"]) | {"status": game["status"]}
                for game in games
            ]
            results = [
                {
                    "homeTeam": {
                        "name": self.get_team_shortname(
                            game["teams"]["home"]["team"]["name"]
                        ),
                        "goals": game["teams"]["home"]["goals"],
                    },
                    "awayTeam": {
                        "name": self.get_team_shortname(
                            game["teams"]["away"]["team"]["name"]
                        ),
                        "goals": game["teams"]["away"]["goals"],
                    },
                    "period": game["currentPeriodOrdinal"]
                    if "currentPeriodOrdinal" in game
                    else None,
                    "status": game["status"],
                }
                for game in games
            ]
            return results
        except Exception:
            logger.exception(f"Error getting results for date {date}")

    def get_upcoming(self):
        """
        Upcoming matches and times
        """
        try:
            games = self.get_games(self.date)
            if games is None:
                logger.warning(f"No games found for date {self.date}")
                return
            for game in games:
                game["homeTeam"] = self.get_team_shortname(game["homeTeam"])
                game["awayTeam"] = self.get_team_shortname(game["awayTeam"])
            return games
        except Exception:
            logger.exception(f"Error getting upcoming matches for date {self.date}")

    def get_standings(self):
        """
        Current standings in Wild Card format
        """
        try:
            wildcards = self.get_wildcards(self.date)
            if len(wildcards) > 0:
                division_leaders = self.get_division_leaders(self.date)
            else:
                division_leaders = self.get_division_leaders(self.date, amount=5)
            standings = {"divisionLeaders": division_leaders, "wildcards": wildcards}
            return standings
        except Exception:
            logger.exception(f"Error getting standings for date {self.date}")

    def get_players_stats(self):
        """
        Player statistics from the latest round
        """
        date = self.date - timedelta(days=1)
        try:
            game_ids = [game["id"] for game in self.get_games(date)]
            games = [self.get_games_boxscore(game_id) for game_id in game_ids]
            player_ids = [game["teams"]["away"]["players"] for game in games]
            player_ids.extend([game["teams"]["home"]["players"] for game in games])
            playersData = [
                elem
                for player in player_ids
                for elem in [
                    value
                    for key, value in player.items()
                    if key.lower().startswith("id")
                ]
            ]
            players = [
                {
                    "firstName": player["person"]["firstName"],
                    "lastName": player["person"]["lastName"],
                    "nationality": player["person"]["nationality"],
                    "team": self.get_team_shortname(
                        player["person"]["currentTeam"]["name"]
                    ),
                    "stats": player["stats"],
                }
                for player in playersData
                if "nationality" in player["person"]
                and "currentTeam" in player["person"]
                and player["stats"]
            ]
            return players
        except Exception:
            logger.exception(f"Error getting players stats for date {date}")

    def get_player_stats(self, name):
        """
        Player season stats with given name
        """
        try:
            team_ids = [team["id"] for team in self.teams.values()]
            rosters = [self.get_roster(id) for id in team_ids]
            players = [player for roster in rosters for player in roster]
            player_id = next(
                (
                    player["id"]
                    for player in players
                    if player["name"].lower() == name.lower()
                ),
                None,
            )
            if player_id is None:
                logger.warn(f"Player not found with name {name}")
                return
            player = self.get_player(player_id)
            player["team"] = self.get_team_shortname(player["team"])
            player["stats"] = self.get_player_season_stats(player_id)
            return player
        except Exception:
            logger.exception(f"Error getting player stats with name {name}")
