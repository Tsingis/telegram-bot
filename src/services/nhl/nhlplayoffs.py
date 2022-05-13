import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from .nhlbase import NHLBase
from ...logger import logging


logger = logging.getLogger(__name__)


class NHLPlayoffs(NHLBase):
    ENVIRONMENT = os.environ["ENVIRONMENT"]
    BRACKET_IMG = Image.open("static/playoffs_template.png")
    BRACKET_FONT = "static/seguibl.ttf"

    def __init__(self):
        super().__init__()
        self.save_img = True if self.ENVIRONMENT.lower() == "local" else False

    def get_bracket(self):
        """
        Creates playoff bracket image for current season
        """
        try:
            playoffs = self.get_playoffs()
            if "rounds" not in playoffs or not playoffs["rounds"]:
                logger.info(f"No playoffs available for season {self.season}")
                return
            series = [
                serie
                for round in playoffs["rounds"]
                for serie in round["series"]
                if "matchupTeams" in serie and serie["round"]["number"] > 0
            ]
            bracket = {
                serie["seriesCode"]: self._get_matchup_info(serie) for serie in series
            }

            # Locations for logos in bracket
            # Round 1
            if "A" in bracket.keys():
                bracket["A"]["location"] = {"top": (1175, 50), "bottom": (1175, 185)}
            if "B" in bracket.keys():
                bracket["B"]["location"] = {"top": (1175, 280), "bottom": (1175, 405)}
            if "C" in bracket.keys():
                bracket["C"]["location"] = {"top": (1175, 505), "bottom": (1175, 625)}
            if "D" in bracket.keys():
                bracket["D"]["location"] = {"top": (1175, 730), "bottom": (1175, 865)}
            if "E" in bracket.keys():
                bracket["E"]["location"] = {"top": (15, 505), "bottom": (15, 625)}
            if "F" in bracket.keys():
                bracket["F"]["location"] = {"top": (15, 730), "bottom": (15, 865)}
            if "G" in bracket.keys():
                bracket["G"]["location"] = {"top": (15, 50), "bottom": (15, 185)}
            if "H" in bracket.keys():
                bracket["H"]["location"] = {"top": (15, 280), "bottom": (15, 405)}

            # Round 2
            if "I" in bracket.keys():
                bracket["I"]["location"] = {"top": (1000, 350), "bottom": (1000, 120)}
                bracket["I"]["matchup"] = {
                    "top": bracket["B"]["winner"],
                    "bottom": bracket["A"]["winner"],
                }
            if "J" in bracket.keys():
                bracket["J"]["location"] = {"top": (1000, 800), "bottom": (1000, 570)}
                bracket["J"]["matchup"] = {
                    "top": bracket["D"]["winner"],
                    "bottom": bracket["C"]["winner"],
                }
            if "K" in bracket.keys():
                bracket["K"]["location"] = {"top": (185, 800), "bottom": (185, 570)}
                bracket["K"]["matchup"] = {
                    "top": bracket["F"]["winner"],
                    "bottom": bracket["E"]["winner"],
                }
            if "L" in bracket.keys():
                bracket["L"]["location"] = {"top": (185, 350), "bottom": (185, 120)}
                bracket["L"]["matchup"] = {
                    "top": bracket["H"]["winner"],
                    "bottom": bracket["G"]["winner"],
                }

            # Round 3, Conference/Semi finals
            if "M" in bracket.keys():
                bracket["M"]["location"] = {"top": (835, 235), "bottom": (835, 675)}
                bracket["M"]["matchup"] = {
                    "top": bracket["I"]["winner"],
                    "bottom": bracket["J"]["winner"],
                }
            if "N" in bracket.keys():
                bracket["N"]["location"] = {"top": (355, 235), "bottom": (355, 675)}
                bracket["N"]["matchup"] = {
                    "top": bracket["L"]["winner"],
                    "bottom": bracket["K"]["winner"],
                }

            # Round 4, Stanley cup final
            if "O" in bracket.keys():
                bracket["O"]["location"] = {"top": (665, 450), "bottom": (530, 450)}
                bracket["O"]["matchup"] = {
                    "top": bracket["M"]["winner"],
                    "bottom": bracket["N"]["winner"],
                }

            # Insert teams into bracket
            for key, value in bracket.items():
                self._insert_team_to_bracket(
                    value["matchup"]["top"], value["location"]["top"]
                )
                self._insert_team_to_bracket(
                    value["matchup"]["bottom"], value["location"]["bottom"]
                )

                if key == "O":
                    text_x_loc = 665
                    text_y_loc = 560
                else:
                    text_x_loc = value["location"]["top"][0] + 70
                    text_y_loc = int(
                        (
                            value["location"]["top"][1]
                            + value["location"]["bottom"][1]
                            + 90
                        )
                        / 2
                    )

                self._insert_status_to_bracket(
                    value["status"], (text_x_loc, text_y_loc)
                )

            # Create in-memory image
            file = BytesIO()
            self.BRACKET_IMG.save(file, "PNG")
            file.seek(0)
            if self.save_img:
                file.name = f"NHL{self.season}.png"
                img = Image.open(file)
                img.save(file.name)
            return file
        except Exception:
            logger.exception("Error getting playoff bracket")

    def _insert_team_to_bracket(self, team, location):
        team_img = Image.open(f"static/NHL_logos/{team}.gif")
        width, height = team_img.size
        team_img = team_img.resize((int(0.9 * width), int(0.9 * height)))
        self.BRACKET_IMG.paste(team_img, location)

    def _insert_status_to_bracket(self, status, location):
        font = ImageFont.truetype(self.BRACKET_FONT, 22)
        text_img = ImageDraw.Draw(self.BRACKET_IMG)
        text_img.text(location, status, anchor="mm", font=font, fill=(0, 0, 0))

    def _get_matchup_info(self, series):
        teams = [team for team in series["matchupTeams"]]
        top_team = next(team["team"]["name"] for team in teams if team["seed"]["isTop"])
        bottom_team = next(
            team["team"]["name"] for team in teams if not team["seed"]["isTop"]
        )
        series_summary = series["currentGame"]["seriesSummary"]
        status = (
            series_summary["seriesStatusShort"]
            if "seriesStatusShort" in series_summary
            else ""
        )
        return {
            "matchup": {
                "top": self.get_team_shortname(top_team),
                "bottom": self.get_team_shortname(bottom_team),
            },
            "status": status,
            "winner": self._get_matchup_winner(teams),
        }

    def _get_matchup_winner(self, matchup_teams):
        for team in matchup_teams:
            if team["seriesRecord"]["wins"] == 4:
                return self.get_team_shortname(team["team"]["name"])
