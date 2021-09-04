from datetime import datetime, timedelta
from .nhlbase import NHLBase
from ..common import convert_timezone
from ...logger import logging


logger = logging.getLogger(__name__)


class NHLAdvanced(NHLBase):
    def __init__(self):
        super().__init__()
        self.teams = self.get_teams()

    # Get match results from the latest round
    def get_results(self):
        date = (self.date - timedelta(days=1)).strftime("%Y-%m-%d")
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
                elif game["currentPeriod"] == 0:
                    period = "Not started"
                else:
                    period = "Live"
                info = {
                    "homeTeam": {
                        "name": game["teams"]["home"]["team"]["name"],
                        "goals": str(game["teams"]["home"]["goals"]),
                    },
                    "awayTeam": {
                        "name": game["teams"]["away"]["team"]["name"],
                        "goals": str(game["teams"]["away"]["goals"]),
                    },
                    "period": period,
                }
                data.append(info)
            return data
        except Exception:
            logger.exception("Error getting results")

    def format_results(self, data):
        results = []
        for game in data:
            period = game["period"]
            # If period is other than OT, SO, Not started or Live use empty string
            if (
                period != "OT"
                and period != "SO"
                and period != "Not started"
                and period != "Live"
            ):
                period = ""
            home = self.teams[game["homeTeam"]["name"]]["shortName"]
            away = self.teams[game["awayTeam"]["name"]]["shortName"]
            results.append(
                f"""{home} {game["homeTeam"]["goals"]} - {game["awayTeam"]["goals"]} {away} {period}""".strip()
            )
        return "\n".join(results)

    # Get upcoming matches and times
    def get_upcoming(self):
        date = self.date.strftime("%Y-%m-%d")
        try:
            games = self.get_games(date)
            return games
        except Exception:
            logger.exception("Error getting upcoming matches")

    def format_upcoming(self, data):
        results = []
        for game in data:
            # Format times to HH:MM
            date = datetime.strptime(game["date"], "%Y-%m-%dT%H:%M:%SZ")
            time = datetime.strftime(
                convert_timezone(date=date, target_tz=self.targetTimezone), "%H:%M"
            )
            home = self.teams[game["homeTeam"]]["shortName"]
            away = self.teams[game["awayTeam"]]["shortName"]
            if game["status"] == "Postponed":
                results.append(f"{home} - {away} Postponed")
            else:
                results.append(f"{home} - {away} at {time}")
        return "\n".join(results)

    # Get current standings in Wild Card format
    def get_standings(self):
        try:
            date = self.date.strftime("%Y-%m-%d")
            wildcards = self.get_wildcards(date)
            if len(wildcards) > 0:
                division_leaders = self.get_division_leaders(date)
            else:
                division_leaders = self.get_division_leaders(date, amount=5)
            standings = {"divisionLeaders": division_leaders, "wildcards": wildcards}
            return standings
        except Exception:
            logger.exception("Error getting standings")

    def format_standings(self, data):
        leaders = sorted(data["divisionLeaders"], key=lambda x: x["conference"])
        wilds = sorted(data["wildcards"], key=lambda x: x["conference"])
        divisions = sorted(
            [
                {
                    "name": item["division"].split(" ")[-1]
                    if " " in item["division"]
                    else item["division"],
                    "conference": item["conference"],
                }
                for item in leaders
            ],
            key=lambda x: x["conference"],
        )

        def format_team_info(data, type, value):
            return next(
                [
                    f"""   {team["name"]} - {team["points"]}/{team["games"]}""".ljust(
                        20, " "
                    )
                    for team in item["teams"]
                ]
                for item in data
                if value in item[type]
            )

        def format_header(text):
            return [f"*{text}*".ljust(25, " ")]

        west = (
            format_header(divisions[0]["name"])
            + format_team_info(leaders, "division", divisions[0]["name"])
            + format_header(divisions[1]["name"])
            + format_team_info(leaders, "division", divisions[1]["name"])
        )

        east = (
            format_header(divisions[2]["name"])
            + format_team_info(leaders, "division", divisions[2]["name"])
            + format_header(divisions[3]["name"])
            + format_team_info(leaders, "division", divisions[3]["name"])
        )

        if len(wilds) > 0:
            west += format_header("Wild Card") + format_team_info(
                wilds, "conference", divisions[0]["conference"]
            )
            east += format_header("Wild Card") + format_team_info(
                wilds, "conference", divisions[2]["conference"]
            )

        standings = "\n".join([e + w for w, e in zip(west, east)])
        return standings

    # Get player statistics from the latest round with nationality
    def get_players_stats(self):
        date = (self.date - timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            game_ids = [game["id"] for game in self.get_games(date)]
            games = [self.get_games_boxscore(game_id) for game_id in game_ids]
            player_ids = [game["teams"]["away"]["players"] for game in games]
            player_ids.extend([game["teams"]["home"]["players"] for game in games])

            # Data for each player
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
                if "nationality" in player["person"] and player["stats"]
            ]
            return players
        except Exception:
            logger.exception("Error getting players stats")

    def format_players_stats(self, data, filter="FIN"):
        players = [
            player
            for player in data
            if player["nationality"] == filter or player["team"] == filter
        ]
        if len(players) > 0:
            # Skaters
            skaters_stats = [
                {
                    "name": skater["lastName"],
                    "team": skater["team"],
                    "goals": skater["stats"]["skaterStats"]["goals"],
                    "assists": skater["stats"]["skaterStats"]["assists"],
                    "timeOnIce": skater["stats"]["skaterStats"]["timeOnIce"],
                }
                for skater in players
                if "skaterStats" in skater["stats"]
            ]

            skaters_stats.sort(key=lambda x: x["name"])
            skaters_stats.sort(
                key=lambda x: (x["goals"] + x["assists"], x["goals"], x["assists"]),
                reverse=True,
            )

            # Goalies
            goalies_stats = [
                {
                    "name": goalie["lastName"],
                    "team": goalie["team"],
                    "saves": goalie["stats"]["goalieStats"]["saves"],
                    "shots": goalie["stats"]["goalieStats"]["shots"],
                    "timeOnIce": goalie["stats"]["goalieStats"]["timeOnIce"],
                }
                for goalie in players
                if "goalieStats" in goalie["stats"]
            ]

            goalies_stats.sort(key=lambda x: x["name"])
            goalies_stats.sort(key=lambda x: (x["saves"], x["shots"]), reverse=True)

            # Skaters stats in format: last name (team) | goals+assists | TOI: MM:SS
            def format_skater_stats(stats):
                return (
                    f"""{stats["name"]} ({stats["team"]}) | {str(stats["goals"])}"""
                    + f"""+{str(stats["assists"])} | TOI: {stats["timeOnIce"]}"""
                )

            # Goalies stats in format: last name (team) | saves/shots | TOI: MM:SS
            def format_goalie_stats(stats):
                return (
                    f"""{stats["name"]} ({stats["team"]}) | {str(stats["saves"])}"""
                    + f"""/{str(stats["shots"])} | TOI: {stats["timeOnIce"]}"""
                )

            skaters_header = "*Skaters:*\n"
            goalies_header = "*Goalies:*\n"

            skaters_texts = [format_skater_stats(stats) for stats in skaters_stats]
            goalies_texts = [format_goalie_stats(stats) for stats in goalies_stats]

            if len(goalies_texts) == 0 and len(skaters_texts) > 0:
                return skaters_header + "\n".join(skaters_texts)
            elif len(skaters_texts) == 0 and len(goalies_texts) > 0:
                return goalies_header + "\n".join(goalies_texts)
            else:
                return (
                    skaters_header
                    + "\n".join(skaters_texts)
                    + "\n"
                    + goalies_header
                    + "\n".join(goalies_texts)
                )
        else:
            return f"Players not found with {filter.upper()}"

    # Extract player stats with given name
    def get_player_stats(self, name):
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

    def format_player_stats(self, data):
        url = f"""https://www.nhl.com/player/{data["name"].replace(" ", "-")}-{data["id"]}"""
        header = f"""{data["name"]} #{data["number"]} {data["position"]} for {data["team"]}\n"""
        if data["stats"] is not None:
            if data["position"] == "Goalie":
                goalie = (
                    f"""GP: {data["stats"]["games"]} | """
                    f"""W: {data["stats"]["wins"]} | """
                    f"""L: {data["stats"]["losses"]} | """
                    f"""OT: {data["stats"]["ot"]} | """
                    f"""Sv: {data["stats"]["saves"]} | """
                    f"""Sv%: {round(data["stats"]["savePercentage"] * 100, 2)} | """
                    f"""GA: {data["stats"]["goalsAgainst"]} | """
                    f"""GAA: {round(data["stats"]["goalAgainstAverage"], 2)} | """
                    f"""SO: {data["stats"]["shutouts"]}"""
                )
                stats = goalie
            else:
                skater = (
                    f"""GP: {data["stats"]["games"]} | """
                    f"""G: {data["stats"]["goals"]} | """
                    f"""A: {data["stats"]["assists"]} | """
                    f"""P: {data["stats"]["points"]} | """
                    f"""Sh%: {round(data["stats"]["shotPct"], 2)} | """
                    f"""+/-: {data["stats"]["plusMinus"]} | """
                    f"""PIM: {data["stats"]["pim"]} | """
                    f"""TOI/G: {data["stats"]["timeOnIcePerGame"]}"""
                )
                stats = skater
            return header + stats + f"\n[Details]({url})"
        return header + f"[Details]({url})"
