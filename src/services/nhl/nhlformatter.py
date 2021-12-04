from datetime import datetime
from .nhlbase import NHLBase
from ..common import convert_timezone


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
        return "\n".join(results)

    def format_upcoming(self, data):
        results = []
        for game in data:
            date = datetime.strptime(game["date"], "%Y-%m-%dT%H:%M:%SZ")
            time = datetime.strftime(
                convert_timezone(date=date, target_tz=self.target_timezone), "%H:%M"
            )
            if game["status"] == "Postponed":
                results.append(f"""{game["homeTeam"]} - {game["awayTeam"]} Postponed""")
            else:
                results.append(f"""{game["homeTeam"]} - {game["awayTeam"]} at {time}""")
        return "\n".join(results)

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

        def format_team_info(data, type, value):
            return next(
                [
                    (
                        f"""   {team["name"]} - {team["points"]} """
                        + f"""({team["record"]["wins"]}-{team["record"]["ot"]}-{team["record"]["losses"]})"""
                    ).ljust(25, " ")
                    for team in item["teams"]
                ]
                for item in data
                if value in item[type]
            )

        def format_header(text):
            return [f"*{text}*".ljust(25, " ")]

        west = (
            format_header(divisions[0]["name"])
            + format_team_info(leaders, "division", divisions[0]["name"])
            + format_header(divisions[1]["name"])
            + format_team_info(leaders, "division", divisions[1]["name"])
        )

        east = (
            format_header(divisions[2]["name"])
            + format_team_info(leaders, "division", divisions[2]["name"])
            + format_header(divisions[3]["name"])
            + format_team_info(leaders, "division", divisions[3]["name"])
        )

        if len(wilds) > 0:
            west += format_header("Wild Card") + format_team_info(
                wilds, "conference", divisions[0]["conference"]
            )
            east += format_header("Wild Card") + format_team_info(
                wilds, "conference", divisions[2]["conference"]
            )

        standings = "\n".join([e + w for w, e in zip(west, east)])
        return standings

    def format_players_stats(self, data, filter="FIN"):
        players = [
            player
            for player in data
            if player["nationality"] == filter or player["team"] == filter
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

            # Skaters stats in format: last name (team) | goals+assists | TOI: MM:SS
            def format_skater_stats(stats):
                return (
                    f"""{stats["name"]} ({stats["team"]}) | {stats["goals"]}"""
                    + f"""+{stats["assists"]} | TOI: {stats["timeOnIce"]}"""
                )

            # Goalies stats in format: last name (team) | saves/shots | TOI: MM:SS
            def format_goalie_stats(stats):
                return (
                    f"""{stats["name"]} ({stats["team"]}) | {stats["saves"]}"""
                    + f"""/{stats["shots"]} | TOI: {stats["timeOnIce"]}"""
                )

            skaters_header = "*Skaters:*\n"
            goalies_header = "*Goalies:*\n"

            skaters_texts = [format_skater_stats(stats) for stats in skaters_stats]
            goalies_texts = [format_goalie_stats(stats) for stats in goalies_stats]

            if len(goalies_texts) == 0 and len(skaters_texts) > 0:
                return skaters_header + "\n".join(skaters_texts)
            elif len(skaters_texts) == 0 and len(goalies_texts) > 0:
                return goalies_header + "\n".join(goalies_texts)
            else:
                return (
                    skaters_header
                    + "\n".join(skaters_texts)
                    + "\n"
                    + goalies_header
                    + "\n".join(goalies_texts)
                )
        else:
            return f"No players available with filter {filter.upper()}"

    def format_player_stats(self, data):
        url = f"""https://www.nhl.com/player/{data["name"].replace(" ", "-")}-{data["id"]}"""
        header = (
            f"""{data["team"]} {data["position"]} #{data["number"]} {data["name"]}\n"""
        )
        if data["stats"] is not None:
            if data["position"] == "Goalie":
                goalie = (
                    f"""GP: {data["stats"]["games"]} | """
                    f"""W: {data["stats"]["wins"]} | """
                    f"""L: {data["stats"]["losses"]} | """
                    f"""OT: {data["stats"]["ot"]} | """
                    f"""Sv: {data["stats"]["saves"]} | """
                    f"""Sv%: {round(data["stats"]["savePercentage"] * 100, 2)} | """
                    f"""GA: {data["stats"]["goalsAgainst"]} | """
                    f"""GAA: {round(data["stats"]["goalAgainstAverage"], 2)} | """
                    f"""SO: {data["stats"]["shutouts"]}"""
                )
                stats = goalie
            else:
                skater = (
                    f"""GP: {data["stats"]["games"]} | """
                    f"""G: {data["stats"]["goals"]} | """
                    f"""A: {data["stats"]["assists"]} | """
                    f"""P: {data["stats"]["points"]} | """
                    f"""Sh%: {round(data["stats"]["shotPct"], 2)} | """
                    f"""+/-: {data["stats"]["plusMinus"]} | """
                    f"""PIM: {data["stats"]["pim"]} | """
                    f"""TOI/G: {data["stats"]["timeOnIcePerGame"]}"""
                )
                stats = skater
            return header + stats + f"\n[Details]({url})"
        return header + f"[Details]({url})"

    def format_player_contract(self, data):
        header = "Contract:\n"
        contract = (
            f"""Year: {data["contract"]["yearStatus"]} | """
            + f"""Cap hit: {data["contract"]["capHit"]} | """
            + f"""Total: {data["contract"]["totalSalary"]}"""
        )
        return header + contract + f"""\n[Details]({data["url"]})"""

    def format_scoring_leaders(self, data):
        leaders = [
            (
                f"""{player["rank"]}. {player["name"].split(" ")[-1]} ({player["team"]})"""
                + f""" | {player["goals"]}+{player["assists"]}={player["points"]}"""
            )
            for player in data
        ]
        return "\n".join(leaders)
