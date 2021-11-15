from datetime import datetime
from .formulaoneadvanced import FormulaOneAdvanced
from ..common import convert_timezone


class FormulaOneFormatter(FormulaOneAdvanced):
    def __init__(self):
        super().__init__()
        self.target_timezone = "Europe/Helsinki"
        self.date_pattern = "%a %B %d at %H:%M"

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
            f"""{result["position"]}. {result["driver"][-3:]} - {self._format_number(result["points"])}"""
            for result in data["driverStandings"]
        ]
        team_standings = [
            f"""{result["position"]}. {result["team"]} - {self._format_number(result["points"])}"""
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
        data["qualifyingTime"] = self._format_date(data["qualifyingTime"])
        data["raceTime"] = self._format_date(data["raceTime"])
        header = f"""Upcoming race: {data["raceNumber"]}/{self.races_amount}"""
        formatted_race_info = (
            f"""{data["raceName"]}\n"""
            + f"""{data["location"]}\n"""
            + f"""Qualifying on {data["qualifyingTime"]}\n"""
            + f"""Race on {data["raceTime"]}"""
        )
        return f"*{header}*\n" + formatted_race_info

    def _format_date(self, date):
        date = convert_timezone(date=date, target_tz=self.target_timezone)
        return datetime.strftime(date, self.date_pattern)

    def _format_number(self, number):
        """
        Formats floating number without insignificant trailing zeroes
        """
        return f"{number:g}"
