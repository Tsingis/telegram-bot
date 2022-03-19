from .nhlbase import NHLBase
from ..utils import (
    format_as_header,
    format_as_code,
    format_as_url,
    escape_special_chars,
    text_to_datetime,
    datetime_to_text,
)


class NHLFormatter(NHLBase):
    def __init__(self):
        super().__init__()

    def format_results(self, data):
        results = []
        for game in data:
            info = ""
            period = game["period"]
            status = game["status"]
            if status in ["Postponed", "Scheduled"]:
                info = status
            elif status == "Final":
                if period in ["SO", "OT"]:
                    info = period
            else:
                info = f"{period} Live"
            home = game["homeTeam"]["name"]
            away = game["awayTeam"]["name"]
            results.append(
                f"""{home} {game["homeTeam"]["goals"]} - {game["awayTeam"]["goals"]} {away} {info}""".strip()
            )

        url = "https://www.nhl.com/scores"
        text = (
            format_as_header("Results:")
            + "\n"
            + format_as_code("\n".join(results))
            + format_as_url(url)
        )
        return text

    def format_upcoming(self, data):
        results = []
        for game in data:

            date = text_to_datetime(game["date"], "%Y-%m-%dT%H:%M:%SZ")
            time = datetime_to_text(date, "%H:%M", self.timezone)
            if game["status"] == "Postponed":
                results.append(f"""{game["homeTeam"]} - {game["awayTeam"]} Postponed""")
            else:
                results.append(f"""{game["homeTeam"]} - {game["awayTeam"]} at {time}""")

        url = "https://www.nhl.com/schedule"
        text = (
            format_as_header("Upcoming matches:")
            + "\n"
            + format_as_code("\n".join(results))
            + format_as_url(url)
        )
        return text

    def format_standings(self, data):
        leaders = sorted(data["divisionLeaders"], key=lambda x: x["conference"])
        wilds = sorted(data["wildcards"], key=lambda x: x["conference"])
        divisions = sorted(
            [
                {
                    "name": item["division"].split(" ")[-1]
                    if " " in item["division"]
                    else item["division"],
                    "conference": item["conference"],
                }
                for item in leaders
            ],
            key=lambda x: x["conference"],
        )

        teams = []
        for leader in leaders:
            teams.extend(leader["teams"])

        max_points = max(teams, key=lambda x: x["points"])
        adjust = len(str(max_points["points"]))

        def format_team_info(data, type, value, left_adjust):
            return next(
                [
                    (
                        f"""{team["name"]} {str(team["points"]).rjust(adjust)} """
                        + f"""{team["record"]["wins"]}-{team["record"]["losses"]}-{team["record"]["ot"]}"""
                    ).ljust(left_adjust)
                    for team in item["teams"]
                ]
                for item in data
                if value in item[type]
            )

        def format_header(text, left_adjust):
            return [f"{text.title()}".ljust(left_adjust)]

        def format_division(division_name, teams, ljust_value):
            division = format_header(division_name, ljust_value)
            division.extend(
                format_team_info(teams, "division", division_name, ljust_value)
            )
            return division

        def format_wildcard(conference_name, teams, ljust_value):
            division = format_header("Wild Card", ljust_value)
            division.extend(
                format_team_info(teams, "conference", conference_name, ljust_value)
            )
            return division

        ljust_value_west = 0
        ljust_value_east = 16

        northwest = format_division(divisions[0]["name"], leaders, ljust_value_west)
        southwest = format_division(divisions[1]["name"], leaders, ljust_value_west)
        northeast = format_division(divisions[2]["name"], leaders, ljust_value_east)
        southeast = format_division(divisions[3]["name"], leaders, ljust_value_east)

        standings = "\n".join([e + w for w, e in zip(northwest, northeast)])
        standings += "\n\n" + "\n".join([e + w for w, e in zip(southwest, southeast)])

        if len(wilds) > 0:
            wilds_west = format_wildcard(
                divisions[0]["conference"], wilds, ljust_value_west
            )
            wilds_east = format_wildcard(
                divisions[2]["conference"], wilds, ljust_value_east
            )
            standings += "\n\n" + "\n".join(
                [e + w for w, e in zip(wilds_west, wilds_east)]
            )

        header = "Standings:"
        url = "https://www.nhl.com/standings"
        return (
            format_as_header(header)
            + "\n"
            + format_as_code(standings)
            + format_as_url(url)
        )

    def format_players_stats(self, data, filter="FIN"):
        players = [
            player
            for player in data
            if player["nationality"] == filter.upper()
            or player["team"] == filter.upper()
        ]
        if len(players) > 0:
            skaters_stats = [
                {
                    "name": skater["lastName"],
                    "team": skater["team"],
                    "goals": skater["stats"]["skaterStats"]["goals"],
                    "assists": skater["stats"]["skaterStats"]["assists"],
                    "timeOnIce": skater["stats"]["skaterStats"]["timeOnIce"],
                }
                for skater in players
                if "skaterStats" in skater["stats"]
            ]

            skaters_stats.sort(key=lambda x: x["name"])
            skaters_stats.sort(
                key=lambda x: (x["goals"] + x["assists"], x["goals"], x["assists"]),
                reverse=True,
            )

            goalies_stats = [
                {
                    "name": goalie["lastName"],
                    "team": goalie["team"],
                    "saves": goalie["stats"]["goalieStats"]["saves"],
                    "shots": goalie["stats"]["goalieStats"]["shots"],
                    "timeOnIce": goalie["stats"]["goalieStats"]["timeOnIce"],
                }
                for goalie in players
                if "goalieStats" in goalie["stats"]
            ]

            goalies_stats.sort(key=lambda x: x["name"])
            goalies_stats.sort(key=lambda x: (x["saves"], x["shots"]), reverse=True)

            # Skaters stats in format: last name (team)|goals+assists|TOI in MM:SS
            def format_skater_stats(stats):
                if len(stats["timeOnIce"]) < 5:
                    stats["timeOnIce"] = "0" + stats["timeOnIce"]
                return (
                    f"""{stats["goals"]}+{stats["assists"]} {stats["timeOnIce"]} """
                    + f"""{stats["name"]} ({stats["team"]})"""
                )

            # Goalies stats in format: last name (team)|saves/shots|TOI in MM:SS
            def format_goalie_stats(stats):
                if len(stats["timeOnIce"]) < 5:
                    stats["timeOnIce"] = "0" + stats["timeOnIce"]
                return (
                    f"""{stats["saves"]}/{stats["shots"]} {stats["timeOnIce"]} """
                    + f"""{stats["name"]} ({stats["team"]})"""
                )

            skaters_header = format_as_header("Skaters:") + "\n"
            goalies_header = format_as_header("Goalies:") + "\n"

            skaters_texts = [format_skater_stats(stats) for stats in skaters_stats]
            goalies_texts = [format_goalie_stats(stats) for stats in goalies_stats]

            if len(goalies_texts) == 0 and len(skaters_texts) > 0:
                return skaters_header + format_as_code("\n".join(skaters_texts))
            elif len(skaters_texts) == 0 and len(goalies_texts) > 0:
                return goalies_header + format_as_code("\n".join(goalies_texts))
            else:
                return (
                    skaters_header
                    + format_as_code("\n".join(skaters_texts))
                    + "\n"
                    + goalies_header
                    + format_as_code("\n".join(goalies_texts))
                )
        else:
            return f"No players available with filter {filter.upper()}"

    def format_player_stats(self, data):
        url = f"""https://www.nhl.com/player/{data["name"].replace(" ", "-")}-{data["id"]}"""
        header = f"""#{data["number"]} {data["position"]} {data["name"]}"""
        info = f"""Team:{data["team"]} From:{data["nationality"]} Age:{data["age"]}"""
        text = (
            format_as_header(escape_special_chars(header))
            + "\n"
            + format_as_code(info)
            + "\n"
        )
        if data["stats"] is not None:
            if data["position"] == "G":
                stats = (
                    f"""GP:{data["stats"]["games"]} """
                    f"""W:{data["stats"]["wins"]} """
                    f"""L:{data["stats"]["losses"]} """
                    f"""OT:{data["stats"]["ot"]}\n"""
                    f"""Sv:{data["stats"]["saves"]} """
                    f"""Sv%:{round(data["stats"]["savePercentage"] * 100, 2)} """
                    f"""SO:{data["stats"]["shutouts"]}\n"""
                    f"""GA:{data["stats"]["goalsAgainst"]} """
                    f"""GAA:{round(data["stats"]["goalAgainstAverage"], 2)}"""
                )
            else:
                stats = (
                    f"""GP:{data["stats"]["games"]} """
                    f"""G:{data["stats"]["goals"]} """
                    f"""A:{data["stats"]["assists"]} """
                    f"""P:{data["stats"]["points"]}\n"""
                    f"""+/-:{data["stats"]["plusMinus"]} """
                    f"""S:{data["stats"]["shots"]} """
                    f"""S%:{round(data["stats"]["shotPct"], 2)}\n"""
                    f"""PIM:{data["stats"]["pim"]} """
                    f"""TOI/G:{data["stats"]["timeOnIcePerGame"]}"""
                )
            text += format_as_header("Stats:") + "\n" + format_as_code(stats)
        text += format_as_url(url)
        return text

    def format_player_contract(self, data):
        contract = (
            f"""Year: {data["contract"]["yearStatus"]}\n"""
            + f"""Cap hit: {data["contract"]["capHit"]}\n"""
            + f"""Total: {data["contract"]["totalSalary"]}"""
        )
        text = (
            format_as_header("Contract:")
            + "\n"
            + format_as_code(contract)
            + format_as_url(data["url"])
        )
        return text

    def format_scoring_leaders(self, data):
        highest_points = max(data, key=lambda x: x["points"])
        highest_points_len = len(str(highest_points["points"]))
        highest_goals = max(data, key=lambda x: x["goals"])
        highest_goals_len = len(str(highest_goals["goals"]))
        highest_assists = max(data, key=lambda x: x["assists"])
        highest_assists_len = len(str(highest_assists["assists"]))

        adjust = highest_goals_len + highest_assists_len + 1

        leaders = [
            (
                f"""{str(player["rank"]).rjust(2)}. """
                + f"""{(str(player["goals"]) + "+" + str(player["assists"])).rjust(adjust)}"""
                + f"""={str(player["points"]).ljust(highest_points_len)} """
                + f"""{player["name"].split(" ")[-1]} ({player["team"]})"""
            )
            for player in data
        ]
        url = "https://www.nhl.com/stats/skaters"
        text = (
            format_as_header("Scoring leaders:")
            + "\n"
            + format_as_code("\n".join(leaders))
            + format_as_url(url)
        )
        return text
