import requests
import datetime as dt
from scripts.common import get_timezone_difference


class NHLBasic:
    BASE_URL = "https://statsapi.web.nhl.com/api/v1/"

    def __init__(self, date=dt.datetime.utcnow()):
        self.date = date + dt.timedelta(hours=get_timezone_difference())

    # Get current season
    def get_season(self):
        month = self.date.month
        year = self.date.year
        if (month < 9):
            return f"{year-1}{year}"
        else:
            return f"{year}{year+1}"

    # Get JSON formatted data from given url
    def get_data(self, url):
        try:
            res = requests.get(url)
            if res.status_code == 200:
                return res.json()
            res.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            print("Error getting data: " + str(ex))
            return None

    # Get team names and abbreviations
    def get_teams(self):
        try:
            data = self.get_data(self.BASE_URL + "/teams")
            return {team["name"]: team["abbreviation"] for team in data["teams"]}
        except Exception as ex:
            print("Error getting teams: " + str(ex))
            return None

    # Get gameIDs for each match on given date
    def get_game_ids(self, date):
        try:
            data = self.get_data(self.BASE_URL + f"/schedule?date={date}")
            return [game["link"].split("/")[-3] for game in data["dates"][0]["games"]]
        except Exception as ex:
            print("Error getting game ids: " + str(ex))
            return None

    # Get data from each match by gameID
    def get_games_linescore(self, game_id):
        try:
            return self.get_data(self.BASE_URL + f"/game/{game_id}/linescore")
        except Exception as ex:
            print("Error getting games linescore: " + str(ex))
            return None

    # Get data from each match by gameID
    def get_games_boxscore(self, game_id):
        try:
            return self.get_data(self.BASE_URL + f"/game/{game_id}/boxscore")
        except Exception as ex:
            print("Error getting games boxscore: " + str(ex))
            return None

    # Get team IDs
    def get_team_ids(self):
        try:
            data = self.get_data(self.BASE_URL + "/teams")
            return [team["id"] for team in data["teams"]]
        except Exception as ex:
            print("Error getting team ids: " + str(ex))
            return None

    # Get rosters with teamID
    def get_roster(self, team_id):
        try:
            data = self.get_data(self.BASE_URL + f"/teams/{team_id}/roster")
            return [{
                "id": player["person"]["id"],
                "name": player["person"]["fullName"]
            } for player in data["roster"]]
        except Exception as ex:
            print("Error getting rosters: " + str(ex))
            return None

    # Get division leaders
    def get_division_leaders(self, date, amount=3):
        try:
            teams = self.get_teams()
            data = self.get_data(self.BASE_URL + f"/standings/byDivision?date={date}")
            # Get divisions
            divs = [
                {
                    "division": div["division"]["name"],
                    "data": div["teamRecords"]
                }
                for div in data["records"]
            ]
            # Get top three leaders on default from each division
            leaders = [{
                "division": div["division"],
                "teams": [
                    {
                        "name": teams[team["team"]["name"]],
                        "points": str(team["points"]),
                        "games": str(team["gamesPlayed"])
                    }
                    for team in div["data"][:amount]
                ]}
                for div in divs]
            return leaders
        except Exception as ex:
            print("Error getting division leaders: " + str(ex))
            return None

    # Get wildcards
    def get_wildcards(self, date, amount=5):
        try:
            teams = self.get_teams()
            data = self.get_data(self.BASE_URL + f"/standings/wildCard?date={date}")
            # Get top five wildcards on default from each conference
            wilds = [{
                "conference": conf["conference"]["name"],
                "teams": [
                    {
                        "name": teams[wild["team"]["name"]],
                        "points": str(wild["points"]),
                        "games": str(wild["gamesPlayed"])
                    }
                    for wild in conf["teamRecords"][:amount]
                ]}
                for conf in data["records"]]
            return wilds
        except Exception as ex:
            print("Error getting wildcards: " + str(ex))
            return None
