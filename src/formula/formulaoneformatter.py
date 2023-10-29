import re
from .formulaoneadvanced import FormulaOneAdvanced
from ..common.utils import (
    datetime_to_text,
    remove_texts,
    format_number,
    format_as_header,
    format_as_code,
    format_as_url,
)


class FormulaOneFormatter(FormulaOneAdvanced):
    def __init__(self):
        super().__init__()
        self.date_pattern = "%b %d"
        self.day_and_time_pattern = "%a %H:%M"
        self.timezone = "Europe/Helsinki"

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
            if len(team_name_parts) <= 2:
                team = team_name_parts[0]
            else:
                team_name_parts_inner = re.sub(
                    r"([A-Z])", r" \1", standing["team"]
                ).split()
                team = " ".join(team_name_parts_inner[:2])
            standing["team"] = team

        driver_standings = [
            f"""{str(result["position"]).rjust(2)}. {result["driver"][-3:]} - {format_number(result["points"])}"""
            for result in data["driverStandings"]
        ]

        longest_team_name = max(
            [len(result["team"]) for result in data["teamStandings"]]
        )
        team_standings = [
            f"""{str(result["position"]).rjust(2)}. {result["team"].ljust(longest_team_name)} - {format_number(result["points"])}"""
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
        date_info = f"{datetime_to_text(first_date, self.date_pattern, target_tz=self.timezone)} to {datetime_to_text(last_date, self.date_pattern, target_tz=self.timezone)}"

        name = remove_texts(data["name"], ["FORMULA 1", str(self.date.year)])
        info = f"""{name}\n""" + f"""{data["location"]}\n""" + date_info

        for session, date in sessions.items():
            info += f"\n{datetime_to_text(date, self.day_and_time_pattern, target_tz=self.timezone)} - {session.title()}"

        text = (
            format_as_header(header)
            + "\n"
            + format_as_code(info)
            + format_as_url(data["raceUrl"])
        )
        return text
