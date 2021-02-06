import datetime as dt
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from .nhlbase import NHLBase
from .common import get_timezone_difference
from ..logger import logging


logger = logging.getLogger(__name__)


class NHLAdvanced(NHLBase):
    def __init__(self, date=dt.datetime.utcnow()):
        super().__init__(date)
        self.season = self.get_season()
        self.teams = self.get_teams()

    # Get match results from the latest round
    def get_results(self):
        date = (self.date - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            gameIds = self.get_game_ids(date)
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
            return None

    def format_results(self, data):
        results = []
        for game in data:
            period = game["period"]
            # If period is other than OT, SO, Not started or Live use empty string
            if (period != "OT" and period != "SO" and period != "Not started" and period != "Live"):
                period = ""
            home = self.teams[game["homeTeam"]["name"]]
            away = self.teams[game["awayTeam"]["name"]]
            results.append(f"""{home} {game["homeTeam"]["goals"]} - {game["awayTeam"]["goals"]} {away} {period}""".strip())
        return "\n".join(results)

    # Get upcoming matches and times
    def get_upcoming(self):
        date = self.date.strftime("%Y-%m-%d")
        try:
            data = self.get_data(self.BASE_URL + f"/schedule?date={date}")
            games = data["dates"][0]["games"]
            data = []
            for game in games:
                info = {
                    "homeTeam": game["teams"]["home"]["team"]["name"],
                    "awayTeam": game["teams"]["away"]["team"]["name"],
                    "date": game["gameDate"],
                    "status": game["status"]["detailedState"]
                }
                data.append(info)
            return data
        except Exception:
            logger.exception("Error getting upcoming matches")
            return None

    def format_upcoming(self, data):
        results = []
        for game in data:
            # Format times to HH:MM
            date = dt.datetime.strptime(game["date"], "%Y-%m-%dT%H:%M:%SZ")
            time = dt.datetime.strftime(date + dt.timedelta(hours=get_timezone_difference(date)), "%H:%M")
            home = self.teams[game["homeTeam"]]
            away = self.teams[game["awayTeam"]]
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
            return {
                "divisionLeaders": divisionLeaders,
                "wildcards": wildcards
            }
        except Exception:
            logger.exception("Error getting standings")
            return None

    def format_standings(self, data):
        leaders = sorted(data["divisionLeaders"], key=lambda x: x["conference"])
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
            west += format_header("Wild Card") + format_team_info(wilds, "conference", divisions[0]["conference"])
            east += format_header("Wild Card") + format_team_info(wilds, "conference", divisions[2]["conference"])

        return "\n".join([e + w for w, e in zip(west, east)])

    # Get player statistics from the latest round with nationality
    def get_players_stats(self):
        date = (self.date - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            gameIds = self.get_game_ids(date)
            games = [self.get_games_boxscore(game_id) for game_id in gameIds]
            playerIds = []
            for game in games:
                playerIds.append(game["teams"]["away"]["players"])
                playerIds.append(game["teams"]["home"]["players"])

            # Data for each player
            players = []
            playersData = [
                elem for player in playerIds for elem in
                [value for key, value in player.items() if key.startswith("ID")]
            ]
            for player in playersData:
                if ("nationality" in player["person"] and player["stats"]):
                    players.append({
                        "firstName": player["person"]["firstName"],
                        "lastName": player["person"]["lastName"],
                        "nationality": player["person"]["nationality"],
                        "team": player["person"]["currentTeam"]["name"],
                        "stats": player["stats"]
                    })
            return players
        except Exception:
            logger.exception("Error getting players stats")
            return None

    def format_players_stats(self, data, nationality="FIN"):
        players = [player for player in data if player["nationality"] == nationality]
        if (len(players) > 0):
            # Skaters stats in format: last name (team) | goals+assists | TOI: MM:SS
            skaters = [player for player in players if "skaterStats" in player["stats"]]
            skatersStats = [
                (f"""{player["lastName"]} ({self.teams[player["team"]]}) | {str(player["stats"]["skaterStats"]["goals"])}"""
                    f"""+{str(player["stats"]["skaterStats"]["assists"])} | TOI: {player["stats"]["skaterStats"]["timeOnIce"]}""")
                for player in skaters
            ]

            # Sort first by name
            skatersStats.sort(key=lambda x: x.split("|")[0])

            # Sort in descending order by points (goals+assists)
            skatersStats.sort(
                key=lambda x: (
                    (int(x.split("|")[1].split("+")[0]) + int(x.split("|")[1].split("+")[-1])),
                    (int(x.split("|")[1].split("+")[0]))),
                reverse=True
            )

            # Goalies stats in format: last name (team) | saves/shots | TOI: MM:SS
            goalies = [player for player in players if "goalieStats" in player["stats"]]
            goaliesStats = [
                (f"""{player["lastName"]} ({self.teams[player["team"]]}) | {str(player["stats"]["goalieStats"]["saves"])}"""
                    f"""/{str(player["stats"]["goalieStats"]["shots"])} | TOI: {player["stats"]["goalieStats"]["timeOnIce"]}""")
                for player in goalies
            ]

            # Sort first by name
            goaliesStats.sort(key=lambda x: x.split("|")[0])

            # Sort in descending order by number of saves out of shots at
            goaliesStats.sort(
                key=lambda x: (
                    int(x.split("|")[1].split("/")[-1]),
                    int(x.split("|")[1].split("/")[0])),
                reverse=True
            )

            skaterHeader = "*Skaters:*\n"
            goalieHeader = "*Goalies:*\n"
            if (len(goaliesStats) == 0 and len(skatersStats) > 0):
                return skaterHeader + "\n".join(skatersStats)
            elif (len(skatersStats) == 0 and len(goaliesStats) > 0):
                return goalieHeader + "\n".join(goaliesStats)
            else:
                return skaterHeader + "\n".join(skatersStats) + "\n" + goalieHeader + "\n".join(goaliesStats)
        else:
            return f"Players not found for {nationality}"

    # Extract player stats with given name
    def get_player_season_stats(self, name):
        playerName = name.strip().lower()
        try:
            teamIds = self.get_team_ids()
            rosters = [self.get_roster(id) for id in teamIds]
            players = [player for roster in rosters for player in roster]
            playerId = next(player["id"] for player in players if player["name"].lower() == playerName)
            player = self.get_data(self.BASE_URL + f"/people/{playerId}/")

            # Extract all stats for given player
            playerData = self.get_data(self.BASE_URL + f"/people/{playerId}/stats?stats=statsSingleSeason&season={self.season}")
            stats = playerData["stats"][0]["splits"][0]["stat"]
            return {
                "id": playerId,
                "name": playerName,
                "team": self.teams[player["people"][0]["currentTeam"]["name"]],
                "position": player["people"][0]["primaryPosition"]["name"],
                "number": player["people"][0]["primaryNumber"],
                "stats": stats
            }
        except Exception:
            logger.exception(f"Error getting player stats for player: {name}")
            return None

    def format_player_season_stats(self, data):
        url = f"""https://www.nhl.com/player/{data["name"].replace(" ", "-")}-{data["id"]}"""
        header = f"""{data["position"]} #{data["number"]} for {data["team"]}\n"""
        if (data["position"] == "Goalie"):
            goalie = (f"""GP: {data["stats"]["games"]} | """
                      f"""W: {data["stats"]["wins"]} | """
                      f"""L: {data["stats"]["losses"]} | """
                      f"""OT: {data["stats"]["ot"]} | """
                      f"""Sv: {data["stats"]["saves"]} | """
                      f"""Sv%: {round(data["stats"]["savePercentage"]*100, 2)} | """
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
    def create_bracket(self):
        def get_series_data(series):
            return {
                "matchup": (self.teams[series["matchupTeams"][0]["team"]["name"]], self.teams[series["matchupTeams"][1]["team"]["name"]]),
                "status": series["currentGame"]["seriesSummary"]["seriesStatusShort"]
                # "top": (series["matchupTeams"][0]["seed"]["isTop"], series["matchupTeams"][1]["seed"]["isTop"])
                # "ranks": (series["matchupTeams"][0]["seed"]["rank"], series["matchupTeams"][1]["seed"]["rank"]),
                # "record": (series["matchupTeams"][0]["seriesRecord"]["wins"], series["matchupTeams"][0]["seriesRecord"]["losses"])
            }

        def insert_team_to_bracket(team, location):
            imgTeam = Image.open(f"static/NHL logos/{team}.gif")
            width, height = imgTeam.size
            imgTeam = imgTeam.resize((int(0.9 * width), int(0.9 * height)))
            imgBracket.paste(imgTeam, location)

        def insert_status_to_bracket(status, location):
            font = ImageFont.truetype("static/seguibl.ttf", 22)
            imgText = ImageDraw.Draw(imgBracket)
            imgText.text(location, status, align="right", font=font, fill=(0, 0, 0))

        try:
            data = self.get_data(self.BASE_URL + f"/tournaments/playoffs?expand=round.series,schedule.game.seriesSummary&season={self.season}")

            # Gather data for each series
            bracket = dict()
            for round in data["rounds"]:
                for series in round["series"]:
                    bracket[series["seriesCode"]] = get_series_data(series)

            # Open blank playoff bracket
            imgBracket = Image.open("static/playoffs_template.png")

            # Locations for logos in bracket
            # Round 1
            bracket["A"]["location"] = [(1175, 50), (1175, 185)]
            bracket["B"]["location"] = [(1175, 280), (1175, 405)]
            bracket["C"]["location"] = [(1175, 505), (1175, 625)]
            bracket["D"]["location"] = [(1175, 730), (1175, 865)]

            bracket["E"]["location"] = [(15, 505), (15, 625)]
            bracket["F"]["location"] = [(15, 730), (15, 865)]
            bracket["G"]["location"] = [(15, 50), (15, 185)]
            bracket["H"]["location"] = [(15, 280), (15, 405)]

            # Round 2
            if (len(bracket) > 8):
                bracket["I"]["location"] = [(1000, 350), (1000, 120)]
                bracket["J"]["location"] = [(1000, 800), (1000, 570)]
                bracket["K"]["location"] = [(185, 800), (185, 570)]
                bracket["L"]["location"] = [(185, 350), (185, 120)]

            # Round 3, Conference finals
            if (len(bracket) > 12):
                bracket["M"]["location"] = [(835, 235), (835, 675)]
                bracket["N"]["location"] = [(355, 235), (355, 675)]

            # Round 4, Stanley cup final
            if (len(bracket) > 14):
                bracket["O"]["location"] = [(665, 450), (530, 450)]

            # Insert teams into bracket
            for key, value in bracket.items():
                insert_team_to_bracket(value["matchup"][0], value["location"][0])
                insert_team_to_bracket(value["matchup"][1], value["location"][1])

                if (key == "O"):
                    textLocX = 600
                    textLocY = 550
                    status = value["status"].rjust(12)
                else:
                    status = value["status"]
                    textLocX = int((value["location"][0][0] + value["location"][1][0]) / 2)
                    textLocY = int((value["location"][0][1] + value["location"][1][1] + 60) / 2)

                insert_status_to_bracket(status, (textLocX, textLocY))

            # Insert champion into bracket
            if ("wins" in bracket["O"]["status"]):
                winner = bracket["O"]["status"][:3]
                imgWinner = Image.open(f"static/NHL logos/{winner}.gif")
                width, height = imgWinner.size
                imgWinner = imgWinner.resize((int(2 * width), int(1.8 * height)))
                imgBracket.paste(imgWinner, (520, 765))

            # Create in-memory image
            filename = f"{self.season}.png"
            file = BytesIO()
            file.name = filename
            imgBracket.save(file, "PNG")
            file.seek(0)
            return file
        except Exception:
            logger.exception("Error getting playoff bracket")
            return None
