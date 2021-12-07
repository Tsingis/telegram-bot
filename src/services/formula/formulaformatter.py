from datetime import datetime
from .formulaoneadvanced import FormulaOneAdvanced
from ..common import convert_timezone, format_as_header, format_as_code, format_as_url


class FormulaOneFormatter(FormulaOneAdvanced):
    def __init__(self):
        super().__init__()
        self.target_timezone = "Europe/Helsinki"
        self.target_datetime_pattern = "on %a %b %d at %H:%M"

    def format_results(self, data):
        url = data["url"]
        race = url.split("/")[-2].replace("-", " ").title()
        formatted_results = [
            f"""{str(result["position"]).rjust(2)}. {result["name"][-3:]} {result["time"]}"""
            for result in data["results"]
        ]

        header = f"Results for {race}:"
        text = (
            format_as_header(header)
            + "\n"
            + format_as_code("\n".join(formatted_results))
            + format_as_url(url)
        )
        return text

    def format_standings(self, data):
        upcoming = self.get_upcoming()
        race_number = upcoming["raceNumber"]
        if self.date <= upcoming["raceTime"]:
            race_number -= 1

        for standing in data["teamStandings"]:
            team_name_parts = standing["team"].split(" ")
            if len(team_name_parts) > 2:
                standing["team"] = " ".join(team_name_parts[:2])
            else:
                standing["team"] = team_name_parts[0]

        driver_standings = [
            f"""{str(result["position"]).rjust(2)}. {result["driver"][-3:]} - {self._format_number(result["points"])}"""
            for result in data["driverStandings"]
        ]

        longest_team_name = max(
            [len(result["team"]) for result in data["teamStandings"]]
        )
        team_standings = [
            f"""{str(result["position"]).rjust(2)}. {result["team"].ljust(longest_team_name)} - {self._format_number(result["points"])}"""
            for result in data["teamStandings"]
        ]

        header = f"Standings {race_number}/{self.races_amount}"
        text = (
            format_as_header(header)
            + "\n"
            + format_as_header("Drivers:")
            + "\n"
            + format_as_code("\n".join(driver_standings))
            + format_as_url(data["driverUrl"])
            + "\n\n"
            + format_as_header("Teams:")
            + "\n"
            + format_as_code("\n".join(team_standings))
            + format_as_url(data["teamUrl"])
        )
        return text

    def format_upcoming(self, data):
        data["qualifyingTime"] = self._format_date(data["qualifyingTime"])
        data["raceTime"] = self._format_date(data["raceTime"])
        header = f"""Upcoming race: {data["raceNumber"]}/{self.races_amount}"""
        formatted_race_info = (
            f"""{data["raceName"]}\n"""
            + f"""{data["location"]}\n"""
            + f"""Qualif {data["qualifyingTime"]}\n"""
            + f"""Race {data["raceTime"]}"""
        )
        text = format_as_header(header) + "\n" + format_as_code(formatted_race_info)
        return text

    def _format_date(self, date):
        date = convert_timezone(date=date, target_tz=self.target_timezone)
        return datetime.strftime(date, self.target_datetime_pattern)

    def _format_number(self, number):
        """
        Formats floating number without insignificant trailing zeroes
        """
        return f"{number:g}"
