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
            game_ids = [game["id"] for game in self.get_games(date)]
            games = [self.get_games_linescore(game_id) for game_id in game_ids]
            data = []
            for game in games:
                if (
                    "currentPeriodTimeRemaining" in game
                    and game["currentPeriodTimeRemaining"] == "Final"
                ):
                    period = game["currentPeriodOrdinal"]
                elif game["currentPeriod"] == 0 or (
                    game["currentPeriod"] == 1
                    and game["currentPeriodTimeRemaining"] == "20:00"
                ):
                    period = "Not started"
                else:
                    period = "Live"
                info = {
                    "homeTeam": {
                        "name": self.teams[game["teams"]["home"]["team"]["name"]][
                            "shortName"
                        ],
                        "goals": game["teams"]["home"]["goals"],
                    },
                    "awayTeam": {
                        "name": self.teams[game["teams"]["away"]["team"]["name"]][
                            "shortName"
                        ],
                        "goals": game["teams"]["away"]["goals"],
                    },
                    "period": period,
                }
                data.append(info)
            return data
        except Exception:
            logger.exception("Error getting results")

    def get_upcoming(self):
        """
        Upcoming matches and times
        """
        try:
            games = self.get_games(self.date)
            for game in games:
                game["homeTeam"] = self.teams[game["homeTeam"]]["shortName"]
                game["awayTeam"] = self.teams[game["awayTeam"]]["shortName"]
            return games
        except Exception:
            logger.exception("Error getting upcoming matches")

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
            logger.exception("Error getting standings")

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
                    value for key, value in player.items() if key.startswith("ID")
                ]
            ]
            players = [
                {
                    "firstName": player["person"]["firstName"],
                    "lastName": player["person"]["lastName"],
                    "nationality": player["person"]["nationality"],
                    "team": self.teams[player["person"]["currentTeam"]["name"]][
                        "shortName"
                    ],
                    "stats": player["stats"],
                }
                for player in playersData
                if "nationality" in player["person"]
                and "currentTeam" in player["person"]
                and player["stats"]
            ]
            return players
        except Exception:
            logger.exception("Error getting players stats")

    def get_player_stats(self, name):
        """
        Player season stats with given name
        """
        try:
            team_ids = [team["id"] for team in self.teams.values()]
            rosters = [self.get_roster(id) for id in team_ids]
            players = [player for roster in rosters for player in roster]
            player_id = next(
                player["id"]
                for player in players
                if player["name"].lower() == name.lower()
            )
            player = self.get_player(player_id)
            player["team"] = self.teams[player["team"]]["shortName"]
            player["stats"] = self.get_player_season_stats(player_id)
            return player
        except Exception:
            logger.exception(f"Error getting player stats for player: {name}")
