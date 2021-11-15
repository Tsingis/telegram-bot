from .formulaoneadvanced import FormulaOneAdvanced
from ..common import format_date, format_number


class FormulaOneFormatter(FormulaOneAdvanced):
    def __init__(self):
        super().__init__()

    def format_results(self, data):
        url = data["url"]
        race = url.split("/")[-2].replace("-", " ").title()
        header = f"Results for {race}:"
        details = f"\n[Details]({url})"
        formatted_results = [
            f"""{result["position"]}. {result["name"][-3:]} {result["time"]}"""
            for result in data["results"]
        ]
        return f"*{header}*\n" + "\n".join(formatted_results) + details

    def format_standings(self, data):
        upcoming = self.get_upcoming()
        race_number = upcoming["raceNumber"]
        if self.date <= upcoming["raceTime"]:
            race_number -= 1

        header = f"""Standings {race_number}/{self.races_amount}"""
        driver_details = f"""\n[Details]({data["driverUrl"]})"""
        team_details = f"""\n[Details]({data["teamUrl"]})"""

        for standing in data["teamStandings"]:
            team_name_parts = standing["team"].split(" ")
            if len(team_name_parts) > 2:
                standing["team"] = " ".join(team_name_parts[:2])
            else:
                standing["team"] = team_name_parts[0]

        driver_standings = [
            f"""{result["position"]}. {result["driver"][-3:]} - {format_number(result["points"])}"""
            for result in data["driverStandings"]
        ]
        team_standings = [
            f"""{result["position"]}. {result["team"]} - {format_number(result["points"])}"""
            for result in data["teamStandings"]
        ]
        formatted_standings = (
            "*Drivers*:\n"
            + "\n".join(driver_standings)
            + driver_details
            + "\n\n*Teams*:\n"
            + "\n".join(team_standings)
            + team_details
        )
        return f"*{header}*\n" + formatted_standings

    def format_upcoming(self, data):
        data["qualifyingTime"] = format_date(data["qualifyingTime"], self.date_pattern)
        data["raceTime"] = format_date(data["raceTime"], self.date_pattern)
        header = f"""Upcoming race: {data["raceNumber"]}/{self.races_amount}"""
        formatted_race_info = (
            f"""{data["raceName"]}\n"""
            + f"""{data["location"]}\n"""
            + f"""Qualifying on {data["qualifyingTime"]}\n"""
            + f"""Race on {data["raceTime"]}"""
        )
        return f"*{header}*\n" + formatted_race_info
