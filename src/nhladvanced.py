import datetime as dt
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from .nhlbasic import NHLBasic
from .common import set_soup, get_timezone_difference


class NHLAdvanced(NHLBasic):
    def __init__(self, date=dt.datetime.utcnow()):
        super().__init__(date)
        self.season = self.get_season()
        self.teams = self.get_teams()

    # Get match results from the latest round
    def get_results(self):
        date = (self.date - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            game_ids = self.get_game_ids(date)
            games = [self.get_games_linescore(game_id) for game_id in game_ids]

            # Extract periods OT/SO for finalized matches or not started/live
            periods = [
                game["currentPeriodOrdinal"] if "currentPeriodTimeRemaining" in game and game["currentPeriodTimeRemaining"] == "Final"
                else "Not started" if game["currentPeriod"] == 0
                else "Live" for game in games
            ]

            # Extract home teams and their goals scored
            home_teams = [
                {
                    "name": team["teams"]["home"]["team"]["name"],
                    "goals": str(team["teams"]["home"]["goals"])
                }
                for team in games
            ]

            # Extract away teams and their goals scored
            away_teams = [
                {
                    "name": team["teams"]["away"]["team"]["name"],
                    "goals": str(team["teams"]["away"]["goals"])
                }
                for team in games
            ]
            return {
                "homeTeams": home_teams,
                "awayTeams": away_teams,
                "periods": periods
            }
        except Exception as ex:
            print("Error getting results: " + str(ex))
            return None

    def format_results(self, data):
        results = []
        for n, period in enumerate(data["periods"]):
            home = data["homeTeams"][n]
            away = data["awayTeams"][n]

            # If period is other than OT, SO, Not started or Live use empty string
            if (period != "OT" and period != "SO" and period != "Not started" and period != "Live"):
                period = ""

            # Replace team names with abbreviations
            if (home["name"] in self.teams):
                home["name"] = self.teams[home["name"]]
            if (away["name"] in self.teams):
                away["name"] = self.teams[away["name"]]

            # Format results in format such as "ANA 5 - 4 TBL OT"
            results.append(f"""{home["name"]} {home["goals"]} - {away["goals"]} {away["name"]} {period}""".strip())
        return "\n".join(results)

    # Get upcoming matches and times
    def get_upcoming(self):
        date = self.date.strftime("%Y-%m-%d")
        try:
            data = self.get_data(self.BASE_URL + f"/schedule?date={date}")
            games_data = data["dates"][0]["games"]
            times = [time["gameDate"] for time in games_data]
            home_teams = [team["teams"]["home"]["team"]["name"] for team in games_data]
            away_teams = [team["teams"]["away"]["team"]["name"] for team in games_data]
            return {
                "homeTeams": home_teams,
                "awayTeams": away_teams,
                "times": times
            }
        except Exception as ex:
            print("Error getting upcoming matches: " + str(ex))
            return None

    def format_upcoming(self, data):
        results = []
        for n, time in enumerate(data["times"]):
            home = data["homeTeams"][n]
            away = data["awayTeams"][n]

            # Format times to HH:MM
            date = dt.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
            time = dt.datetime.strftime(date + dt.timedelta(hours=get_timezone_difference(date)), "%H:%M")

            # Replace team names with abbreviations
            if home in self.teams:
                home = self.teams[home]
            if away in self.teams:
                away = self.teams[away]

            # Format results in format such as "ANA - TBL at 19:00"
            results.append(f"""{home} - {away} at {time}""")
        return "\n".join(results)

    # Get current standings in Wild Card format
    def get_standings(self):
        try:
            date = self.date.strftime("%Y-%m-%d")
            wildcards = self.get_wildcards(date)
            if (len(wildcards) > 0):
                division_leaders = self.get_division_leaders(date)
            else:
                division_leaders = self.get_division_leaders(date, amount=5)
            return {
                "divisionLeaders": division_leaders,
                "wildcards": wildcards
            }
        except Exception as ex:
            print("Error getting standings: " + str(ex))
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
            game_ids = self.get_game_ids(date)
            games = [self.get_games_boxscore(game_id) for game_id in game_ids]
            player_ids = []
            for game in games:
                player_ids.append(game["teams"]["away"]["players"])
                player_ids.append(game["teams"]["home"]["players"])

            # Data for each player
            players = []
            players_data = [
                elem for player in player_ids for elem in
                [value for key, value in player.items() if key.startswith("ID")]
            ]
            for player in players_data:
                if ("nationality" in player["person"] and player["stats"]):
                    players.append({
                        "firstName": player["person"]["firstName"],
                        "lastName": player["person"]["lastName"],
                        "nationality": player["person"]["nationality"],
                        "team": player["person"]["currentTeam"]["name"],
                        "stats": player["stats"]
                    })
            return players
        except Exception as ex:
            print("Error getting players stats: " + str(ex))
            return None

    def format_players_stats(self, data, nationality="FIN"):
        players = [player for player in data if player["nationality"] == nationality]
        if (len(players) > 0):
            # Skaters stats in format: last name (team) | goals+assists | TOI: MM:SS
            skaters = [player for player in players if "skaterStats" in player["stats"]]
            skaters_stats = [
                (f"""{player["lastName"]} ({self.teams[player["team"]]}) | {str(player["stats"]["skaterStats"]["goals"])}"""
                    f"""+{str(player["stats"]["skaterStats"]["assists"])} | TOI: {player["stats"]["skaterStats"]["timeOnIce"]}""")
                for player in skaters
            ]

            # Sort first by name
            skaters_stats.sort(key=lambda x: x.split("|")[0])

            # Sort in descending order by points (goals+assists)
            skaters_stats.sort(
                key=lambda x: (
                    (int(x.split("|")[1].split("+")[0]) + int(x.split("|")[1].split("+")[-1])),
                    (int(x.split("|")[1].split("+")[0]))),
                reverse=True
            )

            # Goalies stats in format: last name (team) | saves/shots | TOI: MM:SS
            goalies = [player for player in players if "goalieStats" in player["stats"]]
            goalies_stats = [
                (f"""{player["lastName"]} ({self.teams[player["team"]]}) | {str(player["stats"]["goalieStats"]["saves"])}"""
                    f"""/{str(player["stats"]["goalieStats"]["shots"])} | TOI: {player["stats"]["goalieStats"]["timeOnIce"]}""")
                for player in goalies
            ]

            # Sort first by name
            goalies_stats.sort(key=lambda x: x.split("|")[0])

            # Sort in descending order by number of saves out of shots at
            goalies_stats.sort(
                key=lambda x: (
                    int(x.split("|")[1].split("/")[-1]),
                    int(x.split("|")[1].split("/")[0])),
                reverse=True
            )

            skater_header = "*Skaters:*\n"
            goalie_header = "*Goalies:*\n"
            if (len(goalies_stats) == 0 and len(skaters_stats) > 0):
                return skater_header + "\n".join(skaters_stats)
            elif (len(skaters_stats) == 0 and len(goalies_stats) > 0):
                return goalie_header + "\n".join(goalies_stats)
            else:
                return skater_header + "\n".join(skaters_stats) + "\n" + goalie_header + "\n".join(goalies_stats)
        else:
            return f"Players not found for {nationality}"

    # Extract player stats with given name
    def get_player_season_stats(self, player_name):
        player_name = player_name.strip().lower()
        try:
            team_ids = self.get_team_ids()
            rosters = [self.get_roster(id) for id in team_ids]
            players = [player for roster in rosters for player in roster]
            player_id = next(player["id"] for player in players if player["name"].lower() == player_name)
            player = self.get_data(self.BASE_URL + f"/people/{player_id}/")

            # Extract all stats for given player
            player_season_data = self.get_data(self.BASE_URL + f"/people/{player_id}/stats?stats=statsSingleSeason&season={self.season}")
            stats = player_season_data["stats"][0]["splits"][0]["stat"]
            return {
                "id": player_id,
                "name": player_name,
                "team": self.teams[player["people"][0]["currentTeam"]["name"]],
                "position": player["people"][0]["primaryPosition"]["name"],
                "number": player["people"][0]["primaryNumber"],
                "stats": stats
            }
        except Exception as ex:
            print("Error getting player stats: " + str(ex))
            return None

    def format_player_season_stats(self, data):
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
            return header + goalie
        else:
            skater = (f"""GP: {data["stats"]["games"]} | """
                      f"""G: {data["stats"]["goals"]} | """
                      f"""A: {data["stats"]["assists"]} | """
                      f"""P: {data["stats"]["points"]} | """
                      f"""Sh%: {round(data["stats"]["shotPct"], 2)} | """
                      f"""+/-: {data["stats"]["plusMinus"]} | """
                      f"""PIM: {data["stats"]["pim"]} | """
                      f"""TOI/G: {data["stats"]["timeOnIcePerGame"]}""")
            return header + skater

    # Get player contract info for current season
    def get_player_contract(self, player_name):
        player_name = player_name.replace(" ", "-").replace("\'", "").lower()
        url = f"https://www.capfriendly.com/players/{player_name}"
        try:
            soup = set_soup(url, target_encoding="utf-8")

            # Find table of current contract
            table = soup.find("table", {"class": "cntrct fixed tbl"})

            # Put data into dataframe
            data = pd.read_html(table.prettify(), flavor="bs4", header=0)[0]

            # Alter season column format
            data["SEASON"] = data["SEASON"].apply(lambda x: x.replace("-", "20"))

            # Filter for current season
            season_mask = data["SEASON"] == self.season

            # Get length, cap hit and total salary of current contract
            contract = {
                "length": f"{data.index[season_mask].values[0] + 1}/{len(data) - 1}",
                "capHit": data["CAP HIT"][season_mask].values[0],
                "totalSalary": data["TOTAL SALARY"][season_mask].values[0],
            }
            return {
                "contract": contract,
                "url": url
            }
        except Exception as ex:
            print("Error getting player contract: " + str(ex))
            return None

    def format_player_contract(self, data):
        return (f"""Year: {data["contract"]["length"]} | """
                f"""Cap hit: {data["contract"]["capHit"]} | """
                f"""Total: {data["contract"]["totalSalary"]}""")

    def format_player_info(self, name, stats, contract):
        result = ""
        if (stats is not None):
            url = f"""https://www.nhl.com/player/{name.replace(" ", "-")}-{stats["id"]}"""
            result += self.format_player_season_stats(stats) + f"\n[Details]({url})"
        if (contract is not None):
            result += "\nContract:\n" + self.format_player_contract(contract) + f"""\n[Details]({contract["url"]})"""
        return result

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
            im_team = Image.open(f"static/NHL logos/{team}.gif")
            width, height = im_team.size
            im_team = im_team.resize((int(0.9 * width), int(0.9 * height)))
            im_bracket.paste(im_team, location)

        def insert_status_to_bracket(status, location):
            font = ImageFont.truetype("static/seguibl.ttf", 22)
            im_text = ImageDraw.Draw(im_bracket)
            im_text.text(location, status, align="right", font=font, fill=(0, 0, 0))

        try:
            data = self.get_data(self.BASE_URL + f"/tournaments/playoffs?expand=round.series,schedule.game.seriesSummary&season={self.season}")

            # Gather data for each series
            bracket = dict()
            for round in data["rounds"]:
                for series in round["series"]:
                    bracket[series["seriesCode"]] = get_series_data(series)

            # Open blank playoff bracket
            im_bracket = Image.open("static/playoffs_template.png")

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
                    text_loc_x = 600
                    text_loc_y = 550
                    status = value["status"].rjust(12)
                else:
                    status = value["status"]
                    text_loc_x = int((value["location"][0][0] + value["location"][1][0]) / 2)
                    text_loc_y = int((value["location"][0][1] + value["location"][1][1] + 60) / 2)

                insert_status_to_bracket(status, (text_loc_x, text_loc_y))

            # Insert champion into bracket
            if ("wins" in bracket["O"]["status"]):
                winner = bracket["O"]["status"][:3]
                im_winner = Image.open(f"static/NHL logos/{winner}.gif")
                width, height = im_winner.size
                im_winner = im_winner.resize((int(2 * width), int(1.8 * height)))
                im_bracket.paste(im_winner, (520, 765))

            # Create in-memory image
            filename = f"{self.season}.png"
            file = BytesIO()
            file.name = filename
            im_bracket.save(file, "PNG")
            file.seek(0)
            return file
        except Exception as ex:
            print("Error getting playoff bracket: " + str(ex))
            return None
