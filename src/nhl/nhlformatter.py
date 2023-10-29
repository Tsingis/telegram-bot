from .nhlbase import NHLBase
from ..common.utils import (
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
            time = datetime_to_text(date, "%H:%M", target_tz=self.timezone)
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
        points_adjust = len(str(max_points["points"]))

        max_games = max(teams, key=lambda x: x["games"])
        games_adjust = len(str(max_games["games"]))

        def format_team_info(data, type, value, adjust_value):
            return next(
                [
                    (
                        f"""{team["name"]} """
                        + f"""{str(team["games"]).rjust(games_adjust)} """
                        + f"""{str(team["points"]).rjust(points_adjust)} """
                        + f"""{team["streak"] if team["streak"] is not None else ""}"""
                    ).ljust(adjust_value)
                    for team in item["teams"]
                ]
                for item in data
                if value in item[type]
            )

        adjust_value_west = 15
        adjust_value_east = 0

        northwest = divisions[2]["name"]
        southwest = divisions[3]["name"]
        northeast = divisions[0]["name"]
        southeast = divisions[1]["name"]

        northwest_teams = format_team_info(
            leaders, "division", northwest, adjust_value_west
        )
        southwest_teams = format_team_info(
            leaders, "division", southwest, adjust_value_west
        )
        northeast_teams = format_team_info(
            leaders, "division", northeast, adjust_value_east
        )
        southeast_teams = format_team_info(
            leaders, "division", southeast, adjust_value_east
        )

        header_north = northwest.title().ljust(adjust_value_west) + northeast.title()
        header_south = (
            "\n" + southwest.title().ljust(adjust_value_west) + southeast.title()
        )

        teams_north = "\n".join(
            [w + e for w, e in zip(northwest_teams, northeast_teams)]
        )
        teams_south = "\n".join(
            [w + e for w, e in zip(southwest_teams, southeast_teams)]
        )

        standings = (
            header_north + "\n" + teams_north + "\n" + header_south + "\n" + teams_south
        )

        if len(wilds) > 0:
            header_text = "Wild Card"
            header_wilds = "\n\n" + header_text.ljust(adjust_value_west) + header_text

            wilds_west_teams = format_team_info(
                wilds, "conference", divisions[2]["conference"], adjust_value_west
            )
            wilds_east_teams = format_team_info(
                wilds, "conference", divisions[0]["conference"], adjust_value_east
            )

            standings += (
                header_wilds
                + "\n"
                + "\n".join([w + e for w, e in zip(wilds_west_teams, wilds_east_teams)])
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
        info = {
            "Team": data["team"],
            "From": data["nationality"],
            "Age": data["age"],
        }
        info_text = (3 * " ").join([f"{key}: {value}" for (key, value) in info.items()])

        if data["stats"] is not None:
            if data["position"] == "G":
                stats = {
                    "GP": data["stats"]["games"],
                    "W": data["stats"]["wins"],
                    "SO": data["stats"]["shutouts"],
                    "Sv%": round(data["stats"]["savePercentage"] * 100, 2),
                    "GAA": round(data["stats"]["goalAgainstAverage"], 2),
                }
            else:
                stats = {
                    "GP": data["stats"]["games"],
                    "G": data["stats"]["goals"],
                    "A": data["stats"]["assists"],
                    "+/-": data["stats"]["plusMinus"],
                    "TOI": data["stats"]["timeOnIcePerGame"],
                }
            stats_text = (3 * " ").join(
                [f"{key}: {value}" for (key, value) in stats.items()]
            )
            info_text += "\n" + stats_text
        text = (
            format_as_header(escape_special_chars(header))
            + "\n"
            + escape_special_chars(info_text)
            + "\n"
            + format_as_url(url)
        )
        return text

    def format_player_contract(self, data):
        contract = {
            "Year": data["contract"]["yearStatus"],
            "Cap": data["contract"]["capHit"],
        }
        contract_text = (3 * " ").join(
            [f"{key}: {value}" for (key, value) in contract.items()]
        )
        text = (
            format_as_header("Contract: ")
            + "\n"
            + escape_special_chars(contract_text)
            + "\n"
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
