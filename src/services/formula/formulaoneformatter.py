from datetime import datetime
from .formulaoneadvanced import FormulaOneAdvanced
from ..utils import convert_timezone, format_as_header, format_as_code, format_as_url


class FormulaOneFormatter(FormulaOneAdvanced):
    def __init__(self):
        super().__init__()
        self.target_timezone = "Europe/Helsinki"
        self.date_pattern = "%b %d"
        self.day_and_time_pattern = "%a at %H:%M"

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
        race_number = upcoming["round"]
        if self.date <= upcoming["sessions"]["race"]:
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
        header = f"""Upcoming race: {data["round"]}/{self.races_amount}"""
        sessions = dict(sorted(data["sessions"].items(), key=lambda x: x[1]))
        first_date, last_date = min(sessions.values()), max(sessions.values())
        date_info = f"{self._format_date(first_date, self.date_pattern)} to {self._format_date(last_date, self.date_pattern)}"

        info = (
            f"""{data["name"]}\n"""
            + date_info
            + f""" in {data["location"]}, {data["country"]}"""
        )

        for session, date in sessions.items():
            info += f"\n{self._format_date(date, self.day_and_time_pattern)} - {session.title()}"

        text = format_as_header(header) + "\n" + format_as_code(info)
        return text

    def _format_date(self, date, pattern):
        date = convert_timezone(date=date, target_tz=self.target_timezone)
        return datetime.strftime(date, pattern)
