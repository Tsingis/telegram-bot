import requests
import datetime as dt


# Get JSON formatted data from given url
def get_data(url):
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    else:
        return None


# Get current season
def get_season():
    month = dt.datetime.utcnow().month
    year = dt.datetime.utcnow().year
    if (month < 9):
        return f"{year-1}{year}"
    else:
        return f"{year}{year+1}"


# Get team names and abbreviations
def get_teams():
    url = "https://statsapi.web.nhl.com/api/v1/teams"
    try:
        data = get_data(url)
        teams_data = data["teams"]
        return {team["name"]: team["abbreviation"] for team in teams_data}
    except Exception:
        return None


# Get gameIDs for each match on given date
def get_game_ids(date):
    url = f"https://statsapi.web.nhl.com/api/v1/schedule?date={date}"
    try:
        data = get_data(url)
        games_data = data["dates"][0]["games"]
        return [game["link"].split("/")[-3] for game in games_data]
    except Exception:
        return None


# Get data from each match by gameID
def get_games_linescore(game_id):
    url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/linescore"
    try:
        return get_data(url)
    except Exception:
        return None


# Get data from each match by gameID
def get_games_boxscore(game_id):
    url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/boxscore"
    try:
        return get_data(url)
    except Exception:
        return None


# Get team IDs
def get_team_ids():
    url = "https://statsapi.web.nhl.com/api/v1/teams"
    try:
        data = get_data(url)
        teams_data = data["teams"]
        return [team["id"] for team in teams_data]
    except Exception:
        return None


# Get rosters with teamID
def get_rosters(team_id):
    url = f"https://statsapi.web.nhl.com/api/v1/teams/{team_id}/roster"
    try:
        data = get_data(url)
        roster = data["roster"]
        return [(player["person"]["fullName"].lower(), player["person"]["id"]) for player in roster]
    except Exception:
        return None


# Get division leaders
def get_division_leaders():
    url = "https://statsapi.web.nhl.com/api/v1/standings/byDivision"
    teams = get_teams()
    try:
        data = get_data(url)["records"]
        # Get divisions
        divs = [
            {
                "name": div["division"]["name"], "data": div["teamRecords"]
            }
            for div in data
        ]
        # Get name and points for top 3 teams in each division
        leaders = [
            {
                "name": div["name"],
                "data": [f"""  {teams[team["team"]["name"]]} - {str(team["points"])}""" for team in div["data"][:3]]
            }
            for div in divs
        ]
        return leaders
    except Exception:
        return None


# Get wildcards
def get_wildcards():
    url = "https://statsapi.web.nhl.com/api/v1/standings/wildCard"
    teams = get_teams()
    try:
        data = get_data(url)["records"]
        # Get top two wildcards from each conference
        wilds = [
            {
                "conf": conf["conference"]["name"],
                "data": [f"""{teams[wild["team"]["name"]]} - {str(wild["points"])}""" for wild in conf["teamRecords"][:4]]
            }
            for conf in data
        ]
        return wilds
    except Exception:
        return None
