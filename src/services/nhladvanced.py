from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from .nhlbase import NHLBase
from .common import convert_timezone
from ..logger import logging


logger = logging.getLogger(__name__)


class NHLAdvanced(NHLBase):
    def __init__(self):
        super().__init__()
        self.teams = self.get_teams()

    # Get match results from the latest round
    def get_results(self):
        date = (self.date - timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            gameIds = [game["id"] for game in self.get_games(date)]
            games = [self.get_games_linescore(game_id) for game_id in gameIds]
            data = []
            for game in games:
                if ("currentPeriodTimeRemaining" in game and
                        game["currentPeriodTimeRemaining"] == "Final"):
                    period = game["currentPeriodOrdinal"]
                elif (game["currentPeriod"] == 0):
                    period = "Not started"
                else:
                    period = "Live"
                info = {
                    "homeTeam": {
                        "name": game["teams"]["home"]["team"]["name"],
                        "goals": str(game["teams"]["home"]["goals"])
                    },
                    "awayTeam": {
                        "name": game["teams"]["away"]["team"]["name"],
                        "goals": str(game["teams"]["away"]["goals"])
                    },
                    "period": period
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
            if (period != "OT" and period != "SO" and period != "Not started" and period != "Live"):
                period = ""
            home = self.teams[game["homeTeam"]["name"]]["shortName"]
            away = self.teams[game["awayTeam"]["name"]]["shortName"]
            results.append(
                f"""{home} {game["homeTeam"]["goals"]} - {game["awayTeam"]["goals"]} {away} {period}""".strip())
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
                convert_timezone(date=date, targetTz=self.targetTimezone), "%H:%M")
            home = self.teams[game["homeTeam"]]["shortName"]
            away = self.teams[game["awayTeam"]]["shortName"]
            if (game["status"] == "Postponed"):
                results.append(f"{home} - {away} Postponed")
            else:
                results.append(f"{home} - {away} at {time}")
        return "\n".join(results)

    # Get current standings in Wild Card format
    def get_standings(self):
        try:
            date = self.date.strftime("%Y-%m-%d")
            wildcards = self.get_wildcards(date)
            if (len(wildcards) > 0):
                divisionLeaders = self.get_division_leaders(date)
            else:
                divisionLeaders = self.get_division_leaders(date, amount=5)
            standings = {
                "divisionLeaders": divisionLeaders,
                "wildcards": wildcards
            }
            return standings
        except Exception:
            logger.exception("Error getting standings")

    def format_standings(self, data):
        leaders = sorted(data["divisionLeaders"],
                         key=lambda x: x["conference"])
        wilds = sorted(data["wildcards"], key=lambda x: x["conference"])
        divisions = sorted([
            {
                "name": item["division"].split(" ")[-1] if " " in item["division"] else item["division"],
                "conference": item["conference"]
            } for item in leaders], key=lambda x: x["conference"])

        def format_team_info(data, type, value):
            return next(
                [f"""   {team["name"]} - {team["points"]}/{team["games"]}""".ljust(20, " ")
                 for team in item["teams"]]
                for item in data if value in item[type])

        def format_header(text):
            return [f"*{text}*".ljust(25, " ")]

        west = (format_header(divisions[0]["name"]) + format_team_info(leaders, "division", divisions[0]["name"]) +
                format_header(divisions[1]["name"]) + format_team_info(leaders, "division", divisions[1]["name"]))

        east = (format_header(divisions[2]["name"]) + format_team_info(leaders, "division", divisions[2]["name"]) +
                format_header(divisions[3]["name"]) + format_team_info(leaders, "division", divisions[3]["name"]))

        if (len(wilds) > 0):
            west += format_header("Wild Card") + format_team_info(wilds,
                                                                  "conference", divisions[0]["conference"])
            east += format_header("Wild Card") + format_team_info(wilds,
                                                                  "conference", divisions[2]["conference"])

        standings = "\n".join([e + w for w, e in zip(west, east)])
        return standings

    # Get player statistics from the latest round with nationality
    def get_players_stats(self):
        date = (self.date - timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            gameIds = [game["id"] for game in self.get_games(date)]
            games = [self.get_games_boxscore(game_id) for game_id in gameIds]
            playerIds = [game["teams"]["away"]["players"] for game in games]
            playerIds.extend(
                [game["teams"]["home"]["players"] for game in games])

            # Data for each player
            playersData = [
                elem for player in playerIds for elem in
                [value for key, value in player.items() if key.startswith("ID")]
            ]
            players = [{
                "firstName": player["person"]["firstName"],
                "lastName": player["person"]["lastName"],
                "nationality": player["person"]["nationality"],
                "team": self.teams[player["person"]["currentTeam"]["name"]]["shortName"],
                "stats": player["stats"]
            } for player in playersData if "nationality" in player["person"] and player["stats"]]
            return players
        except Exception:
            logger.exception("Error getting players stats")

    def format_players_stats(self, data, filter="FIN"):
        players = [player for player in data if player["nationality"]
                   == filter or player["team"] == filter]
        if (len(players) > 0):
            # Skaters
            skatersStats = [{
                "name": skater["lastName"],
                "team": skater["team"],
                "goals": skater["stats"]["skaterStats"]["goals"],
                "assists": skater["stats"]["skaterStats"]["assists"],
                "timeOnIce": skater["stats"]["skaterStats"]["timeOnIce"]
            } for skater in players if "skaterStats" in skater["stats"]]

            skatersStats.sort(key=lambda x: x["name"])
            skatersStats.sort(key=lambda x: (x["goals"] + x["assists"], x["goals"], x["assists"]),
                              reverse=True)

            # Goalies
            goaliesStats = [{
                "name": goalie["lastName"],
                "team": goalie["team"],
                "saves": goalie["stats"]["goalieStats"]["saves"],
                "shots": goalie["stats"]["goalieStats"]["shots"],
                "timeOnIce": goalie["stats"]["goalieStats"]["timeOnIce"]
            } for goalie in players if "goalieStats" in goalie["stats"]]

            goaliesStats.sort(key=lambda x: x["name"])
            goaliesStats.sort(key=lambda x: (
                x["saves"], x["shots"]), reverse=True)

            # Skaters stats in format: last name (team) | goals+assists | TOI: MM:SS
            def format_skater_stats(stats):
                return (f"""{stats["name"]} ({stats["team"]}) | {str(stats["goals"])}""" +
                        f"""+{str(stats["assists"])} | TOI: {stats["timeOnIce"]}""")

            # Goalies stats in format: last name (team) | saves/shots | TOI: MM:SS
            def format_goalie_stats(stats):
                return (f"""{stats["name"]} ({stats["team"]}) | {str(stats["saves"])}""" +
                        f"""/{str(stats["shots"])} | TOI: {stats["timeOnIce"]}""")

            skatersHeader = "*Skaters:*\n"
            goaliesHeader = "*Goalies:*\n"

            skatersTexts = [format_skater_stats(
                stats) for stats in skatersStats]
            goaliesTexts = [format_goalie_stats(
                stats) for stats in goaliesStats]

            if (len(goaliesTexts) == 0 and len(skatersTexts) > 0):
                return skatersHeader + "\n".join(skatersTexts)
            elif (len(skatersTexts) == 0 and len(goaliesTexts) > 0):
                return goaliesHeader + "\n".join(goaliesTexts)
            else:
                return skatersHeader + "\n".join(skatersTexts) + "\n" + goaliesHeader + "\n".join(goaliesTexts)
        else:
            return f"Players not found with {filter.upper()}"

    # Extract player stats with given name
    def get_player_stats(self, name):
        try:
            teamIds = [team["id"] for team in self.teams.values()]
            rosters = [self.get_roster(id) for id in teamIds]
            players = [player for roster in rosters for player in roster]
            playerId = next(
                player["id"] for player in players if player["name"].lower() == name.lower())
            player = self.get_player(playerId)
            player["team"] = self.teams[player["team"]]["shortName"]
            player["stats"] = self.get_player_season_stats(playerId)
            return player
        except Exception:
            logger.exception(f"Error getting player stats for player: {name}")

    def format_player_stats(self, data):
        url = f"""https://www.nhl.com/player/{data["name"].replace(" ", "-")}-{data["id"]}"""
        header = f"""{data["name"]} #{data["number"]} {data["position"]} for {data["team"]}\n"""
        if (data["position"] == "Goalie"):
            goalie = (f"""GP: {data["stats"]["games"]} | """
                      f"""W: {data["stats"]["wins"]} | """
                      f"""L: {data["stats"]["losses"]} | """
                      f"""OT: {data["stats"]["ot"]} | """
                      f"""Sv: {data["stats"]["saves"]} | """
                      f"""Sv%: {round(data["stats"]["savePercentage"] * 100, 2)} | """
                      f"""GA: {data["stats"]["goalsAgainst"]} | """
                      f"""GAA: {round(data["stats"]["goalAgainstAverage"], 2)} | """
                      f"""SO: {data["stats"]["shutouts"]}""")
            stats = goalie
        else:
            skater = (f"""GP: {data["stats"]["games"]} | """
                      f"""G: {data["stats"]["goals"]} | """
                      f"""A: {data["stats"]["assists"]} | """
                      f"""P: {data["stats"]["points"]} | """
                      f"""Sh%: {round(data["stats"]["shotPct"], 2)} | """
                      f"""+/-: {data["stats"]["plusMinus"]} | """
                      f"""PIM: {data["stats"]["pim"]} | """
                      f"""TOI/G: {data["stats"]["timeOnIcePerGame"]}""")
            stats = skater
        return header + stats + f"\n[Details]({url})"

    # Creates playoff bracket for current season
    def get_bracket(self):
        def get_series_data(series):
            teams = [team for team in series["matchupTeams"]]
            topTeam = next(team["team"]["name"]
                           for team in teams if team["seed"]["isTop"])
            bottomTeam = next(team["team"]["name"]
                              for team in teams if not team["seed"]["isTop"])
            winner = get_winner_from_teams(teams)
            return {
                "matchup": {
                    "top": self.teams[topTeam]["shortName"],
                    "bottom": self.teams[bottomTeam]["shortName"]
                },
                "status": series["currentGame"]["seriesSummary"]["seriesStatusShort"],
                "winner": winner
            }

        def insert_team_to_bracket(team, location):
            imgTeam = Image.open(f"static/NHL_logos/{team}.gif")
            width, height = imgTeam.size
            imgTeam = imgTeam.resize((int(0.9 * width), int(0.9 * height)))
            imgBracket.paste(imgTeam, location)

        def insert_status_to_bracket(status, location):
            font = ImageFont.truetype("static/seguibl.ttf", 22)
            imgText = ImageDraw.Draw(imgBracket)
            imgText.text(location, status, anchor="mm",
                         font=font, fill=(0, 0, 0))

        def get_winner_from_teams(teams):
            for team in teams:
                if team["seriesRecord"]["wins"] == 4:
                    return self.teams[team["team"]["name"]]["shortName"]

        try:
            data = self.get_playoffs()
            bracket = dict()
            for round in data["rounds"]:
                for series in round["series"]:
                    if "matchupTeams" in series and series["round"]["number"] > 0:
                        bracket[series["seriesCode"]
                                ] = get_series_data(series)

            # Open blank playoff bracket
            imgBracket = Image.open("static/playoffs_template.png")

            # Locations for logos in bracket
            # Round 1
            if ("A" in bracket.keys()):
                bracket["A"]["location"] = {
                    "top": (1175, 50), "bottom": (1175, 185)}
            if ("B" in bracket.keys()):
                bracket["B"]["location"] = {
                    "top": (1175, 280), "bottom": (1175, 405)}
            if ("C" in bracket.keys()):
                bracket["C"]["location"] = {
                    "top": (1175, 505), "bottom": (1175, 625)}
            if ("D" in bracket.keys()):
                bracket["D"]["location"] = {
                    "top": (1175, 730), "bottom": (1175, 865)}
            if ("E" in bracket.keys()):
                bracket["E"]["location"] = {
                    "top": (15, 505), "bottom": (15, 625)}
            if ("F" in bracket.keys()):
                bracket["F"]["location"] = {
                    "top": (15, 730), "bottom": (15, 865)}
            if ("G" in bracket.keys()):
                bracket["G"]["location"] = {
                    "top": (15, 50), "bottom": (15, 185)}
            if ("H" in bracket.keys()):
                bracket["H"]["location"] = {
                    "top": (15, 280), "bottom": (15, 405)}

            # Round 2
            if ("I" in bracket.keys()):
                bracket["I"]["location"] = {
                    "top": (1000, 350), "bottom": (1000, 120)}
                bracket["I"]["matchup"] = {
                    "top": bracket["B"]["winner"],
                    "bottom": bracket["A"]["winner"]
                }
            if ("J" in bracket.keys()):
                bracket["J"]["location"] = {
                    "top": (1000, 800), "bottom": (1000, 570)}
                bracket["J"]["matchup"] = {
                    "top": bracket["D"]["winner"],
                    "bottom": bracket["C"]["winner"]
                }
            if ("K" in bracket.keys()):
                bracket["K"]["location"] = {
                    "top": (185, 800), "bottom": (185, 570)}
                bracket["K"]["matchup"] = {
                    "top": bracket["F"]["winner"],
                    "bottom": bracket["E"]["winner"]
                }
            if ("L" in bracket.keys()):
                bracket["L"]["location"] = {
                    "top": (185, 350), "bottom": (185, 120)}
                bracket["L"]["matchup"] = {
                    "top": bracket["H"]["winner"],
                    "bottom": bracket["G"]["winner"]
                }

            # Round 3
            if ("M" in bracket.keys()):
                bracket["M"]["location"] = {
                    "top": (835, 235), "bottom": (835, 675)}
                bracket["M"]["matchup"] = {
                    "top": bracket["I"]["winner"],
                    "bottom": bracket["J"]["winner"]
                }
            if ("N" in bracket.keys()):
                bracket["N"]["location"] = {
                    "top": (355, 235), "bottom": (355, 675)}
                bracket["N"]["matchup"] = {
                    "top": bracket["L"]["winner"],
                    "bottom": bracket["K"]["winner"]
                }

            # Round 4, Stanley cup final
            if ("O" in bracket.keys()):
                bracket["O"]["location"] = {
                    "top": (665, 450), "bottom": (530, 450)}
                bracket["O"]["matchup"] = {
                    "top": bracket["M"]["winner"],
                    "bottom": bracket["N"]["winner"]
                }

            # Insert teams into bracket
            for key, value in bracket.items():
                if (key == "O"):
                    textLocX = 665
                    textLocY = 560
                else:
                    textLocX = value["location"]["top"][0] + 70
                    textLocY = int((value["location"]["top"]
                                   [1] + value["location"]["bottom"][1] + 90) / 2)

                insert_team_to_bracket(
                    value["matchup"]["top"], value["location"]["top"])
                insert_team_to_bracket(
                    value["matchup"]["bottom"], value["location"]["bottom"])
                insert_status_to_bracket(value["status"], (textLocX, textLocY))

            # Create in-memory image
            filename = f"{self.season}.png"
            file = BytesIO()
            file.name = filename
            imgBracket.save(file, "PNG")
            file.seek(0)
            # test = Image.open(file)
            # test.save(f"{filename}")
            return file
        except Exception:
            logger.exception("Error getting playoff bracket")
