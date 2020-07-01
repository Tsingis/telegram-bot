import datetime as dt
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from scripts.nhlbasic import NHLBasic
from scripts.common import set_soup


class NHLAdvanced(NHLBasic):
    def __init__(self, date=dt.datetime.utcnow()):
        super().__init__(date)
        self.season = self.get_season()
        self.teams = self.get_teams()

    # Get match results from the latest round
    def get_results(self):
        date = (self.date - dt.timedelta(days=1)).strftime("%Y-%m-%d")

        def format_results(home, away, period):
            # If period is other than OT, SO, Not started or Live use empty string
            if (period != "OT" and period != "SO" and period != "Not started" and period != "Live"):
                period = ""

            # Replace team names with abbreviations
            if (home["name"] in self.teams):
                home["name"] = self.teams[home["name"]]
            if (away["name"] in self.teams):
                away["name"] = self.teams[away["name"]]

            # Format results in format such as "ANA 5 - 4 TBL OT"
            return f"""{home["name"]} {home["goals"]} - {away["goals"]} {away["name"]} {period}"""

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

            return [format_results(home_teams[n], away_teams[n], periods[n]).strip() for n in range(len(periods))]
        except Exception as ex:
            print("Error getting results: " + str(ex))
            return None

    # Get upcoming matches and times
    def get_upcoming(self):
        date = self.date.strftime("%Y-%m-%d")

        def format_schedule(home, away, time):
            # Replace team names with abbreviations
            if home in self.teams:
                home = self.teams[home]
            if away in self.teams:
                away = self.teams[away]
            # Format results in format such as "ANA - TBL at 19:00"
            return f"""{home} - {away} at {time}"""

        # Convert match date to time in HH:MM format
        def date_to_time(date):
            date = dt.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
            # Some poor man timezone handling
            if (dt.datetime(2020, 3, 29, 3) < date < dt.datetime(2020, 10, 25, 4)
                or dt.datetime(2019, 3, 31, 3) < date < dt.datetime(2019, 10, 27, 4)):
                hours = 3
            else:
                hours = 2
            date = date + dt.timedelta(hours=hours)
            return f"{date.hour:d}:{date.minute:02d}"

        try:
            data = self.get_data(self.BASE_URL + f"/schedule?date={date}")
            games_data = data["dates"][0]["games"]

            # Extract dates
            times = [date_to_time(time["gameDate"]) for time in games_data]

            home_teams = [team["teams"]["home"]["team"]["name"] for team in games_data]
            away_teams = [team["teams"]["away"]["team"]["name"] for team in games_data]

            return [format_schedule(home_teams[n], away_teams[n], times[n]) for n in range(len(times))]
        except Exception as ex:
            print("Error getting upcoming matches: " + str(ex))
            return None

    # Get current standings in Wild Card format
    def get_standings(self):
        # Format results (team - points) in two columns, eastern and western with
        # their respective divisions and wild card spots and contenders
        def format_results(leaders, wilds):
            east = (["EAST"] + [leaders[0]["name"]] + leaders[0]["data"]
                    + [leaders[1]["name"]] + leaders[1]["data"]
                    + ["Wild Card"] + wilds[0]["data"])

            west = (["WEST"] + [leaders[2]["name"]] + leaders[2]["data"]
                    + [leaders[3]["name"]] + leaders[3]["data"]
                    + ["Wild Card"] + wilds[1]["data"])

            # Make first column 20 chars wide for slightly better formatting
            west = list(map(lambda x: x.ljust(23, " "), west))
            return ["".join(result) for result in zip(west, east)]

        try:
            return format_results(self.get_division_leaders(), self.get_wildcards())
        except Exception as ex:
            print("Error getting standings: " + str(ex))
            return None

    # Get Finnish player statistics from the latest round
    def get_finns(self):
        date = (self.date - dt.timedelta(days=1)).strftime("%Y-%m-%d")

        # Extract last name, stats and team name for each Finnish player
        def extract_finns(side):
            players_side = [player["teams"][side]["players"] for player in games]

            players_stats = [
                [
                    (value["person"]["lastName"], value["stats"], value["person"]["currentTeam"]["name"])
                    for key, value in players_side[n].items() if key.startswith("ID")
                    and "nationality" in value["person"]  # if nationality key exists
                    and value["person"]["nationality"] == "FIN"  # if player is Finnish
                    and value["stats"]  # if player was in line-up
                ]
                for n in range(len(players_side))
            ]

            # Remove empty elements
            players_stats = [elem for elem in players_stats if elem]

            # Flatten player stats list
            return [elem for sublist in players_stats for elem in sublist]

        try:
            game_ids = self.get_game_ids(date)
            games = [self.get_games_boxscore(game_id) for game_id in game_ids]

            finns = extract_finns("away") + extract_finns("home")

            # Skaters stats in format: last name (team) | goals+assists | TOI: MM:SS
            skaters = [player for player in finns if "skaterStats" in player[1]]
            skaters_stats = [
                (f"""{player[0]} ({self.teams[player[2]]}) | {str(player[1]["skaterStats"]["goals"])}"""
                 f"""+{str(player[1]["skaterStats"]["assists"])} | TOI: {player[1]["skaterStats"]["timeOnIce"]}""")
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
            goalies = [player for player in finns if "goalieStats" in player[1]]
            goalies_stats = [
                (f"""{player[0]} ({self.teams[player[2]]}) | {str(player[1]["goalieStats"]["saves"])}"""
                 f"""/{str(player[1]["goalieStats"]["shots"])} | TOI: {player[1]["goalieStats"]["timeOnIce"]}""")
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

            return skaters_stats, goalies_stats
        except Exception as ex:
            print("Error getting Finnish players: " + str(ex))
            return None, None

    # Extract player stats with given name
    def get_player_stats(self, player_name):

        # Capitalize player first name and last name
        player_name = player_name.lower().strip()

        # Extract and format specific stats for player (goalie or skater)
        def format_stats(stats, player_position):
            # Check if player is goalie
            if (player_position == "Goalie"):
                goalie_stats = (f"""GP: {stats["games"]} | """
                                f"""W: {stats["wins"]} | """
                                f"""Sv: {stats["saves"]} | """
                                f"""Sv%: {round(stats["savePercentage"]*100, 2)} | """
                                f"""GA: {stats["goalsAgainst"]} | """
                                f"""GAA: {round(stats["goalAgainstAverage"], 2)} | """
                                f"""SO: {stats["shutouts"]}""")
                return goalie_stats
            else:
                skater_stats = (f"""GP: {stats["games"]} | """
                                f"""G: {stats["goals"]} | """
                                f"""A: {stats["assists"]} | """
                                f"""P: {stats["points"]} | """
                                f"""Sh%: {round(stats["shotPct"], 2)} | """
                                f"""+/-: {stats["plusMinus"]} | """
                                f"""TOI/G: {stats["timeOnIcePerGame"]}""")
                return skater_stats

        try:
            team_ids = self.get_team_ids()
            rosters = [self.get_rosters(id) for id in team_ids]
            players = [elem for sublist in rosters for elem in sublist]
            player_id = [player[1] for player in players if player[0] == player_name][0]

            # Extract team and position for given player
            data = self.get_data(self.BASE_URL + f"/people/{player_id}/")
            player_team = self.teams[data["people"][0]["currentTeam"]["name"]]
            player_position = data["people"][0]["primaryPosition"]["name"]
            player_number = data["people"][0]["primaryNumber"]

            # Extract all stats for given player
            data = self.get_data(self.BASE_URL + f"/people/{player_id}/stats?stats=statsSingleSeason&season={self.season}")
            stats = data["stats"][0]["splits"][0]["stat"]

            player_info = f"{player_position} #{player_number} for {player_team}\n"
            player_stats = player_info + format_stats(stats, player_position)
            return {
                "id": player_id,
                "data": player_stats
            }
        except Exception as ex:
            print("Error getting player stats: " + str(ex))
            return None, None

    # Creates playoff bracket for current season
    def create_bracket(self):

        def get_series_data(series):
            series = {
                "matchup": (self.teams[series["matchupTeams"][0]["team"]["name"]], self.teams[series["matchupTeams"][1]["team"]["name"]]),
                "status": series["currentGame"]["seriesSummary"]["seriesStatusShort"]
                # "top": (series["matchupTeams"][0]["seed"]["isTop"], series["matchupTeams"][1]["seed"]["isTop"])
                # "ranks": (series["matchupTeams"][0]["seed"]["rank"], series["matchupTeams"][1]["seed"]["rank"]),
                # "record": (series["matchupTeams"][0]["seriesRecord"]["wins"], series["matchupTeams"][0]["seriesRecord"]["losses"])
            }
            return series

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
            im_bracket = Image.open("static/NHL logos/playoffs.png")

            # bracket.pop("I", None)
            # bracket.pop("J", None)
            # bracket.pop("K", None)
            # bracket.pop("L", None)
            # bracket.pop("M", None)
            # bracket.pop("N", None)
            # bracket.pop("O", None)

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
            # test = Image.open(file)
            # test.save(f"{filename}")
            return file
        except Exception as ex:
            print("Error getting playoff bracket: " + str(ex))
            return None

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
            contract_info = {
                "Length": f"{data.index[season_mask].values[0] + 1}/{len(data) - 1}",
                "Cap hit": data["CAP HIT"][season_mask].values[0],
                "Total salary": data["TOTAL SALARY"][season_mask].values[0],
            }

            # Format info
            player_contract = (f"""Year: {contract_info["Length"]} | """
                               f"""Cap hit: {contract_info["Cap hit"]} | """
                               f"""Total: {contract_info["Total salary"]}""")
            return {
                "data": player_contract,
                "url": url
            }
        except Exception as ex:
            print("Error getting player contract: " + str(ex))
            return None

    def format_player_info(self, name, stats, contract):
        url = f"""https://www.nhl.com/player/{name.replace(" ", "-")}-{stats["id"]}"""
        msg = stats["data"] + f"\n[Details]({url})"
        if (contract is not None):
            msg = msg + "\nContract:\n" + contract["data"] + f"""\n[Details]({contract["url"]})"""
        return msg
