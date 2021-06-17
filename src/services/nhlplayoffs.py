import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from .nhlbase import NHLBase
from ..logger import logging


logger = logging.getLogger(__name__)


class NHLPlayoffs(NHLBase):
    ENVIRONMENT = os.environ["ENVIRONMENT"]
    LOGO_LOCATIONS = {
        "1": {"top": (1175, 50), "bottom": (1175, 185)},
        "2": {"top": (1175, 280), "bottom": (1175, 405)},
        "3": {"top": (1175, 730), "bottom": (1175, 865)},
        "4": {"top": (1175, 505), "bottom": (1175, 625)},
        "5": {"top": (15, 730), "bottom": (15, 865)},
        "6": {"top": (15, 505), "bottom": (15, 625)},
        "7": {"top": (15, 50), "bottom": (15, 185)},
        "8": {"top": (15, 280), "bottom": (15, 405)},
        "9": {"top": (1000, 350), "bottom": (1000, 120)},
        "10": {"top": (1000, 570), "bottom": (1000, 800)},
        "11": {"top": (185, 570), "bottom": (185, 800)},
        "12": {"top": (185, 350), "bottom": (185, 120)},
        "13": {"top": (835, 235), "bottom": (835, 675)},
        "14": {"top": (355, 235), "bottom": (355, 675)},
        "15": {"top": (665, 450), "bottom": (530, 450)}
    }
    BRACKET_IMG = Image.open("static/playoffs_template.png")
    BRACKET_FONT = "static/seguibl.ttf"

    def __init__(self):
        super().__init__()
        self.teams = self.get_teams()
        self.bracketImg = Image.open("static/playoffs_template.png")
        self.font = "static/seguibl.ttf"
        self.matchups = []
        self.series = []
        self.saveImg = True if self.ENVIRONMENT == "LOCAL" else False

    # Creates playoff bracket for current season
    def get_bracket(self):
        try:
            playoffs = self.get_playoffs()
            self.series = [serie for round in playoffs["rounds"] for serie in round["series"]
                           if "matchupTeams" in serie and serie["round"]["number"] > 0]

            # Round 1
            for serie in self.series:
                if (serie["seriesCode"] == "A"):
                    self._add_matchup("1", serie)
                if (serie["seriesCode"] == "B"):
                    self._add_matchup("2", serie)
                if (serie["seriesCode"] == "C"):
                    self._add_matchup("3", serie)
                if (serie["seriesCode"] == "D"):
                    self._add_matchup("4", serie)
                if (serie["seriesCode"] == "E"):
                    self._add_matchup("5", serie)
                if (serie["seriesCode"] == "F"):
                    self._add_matchup("6", serie)
                if (serie["seriesCode"] == "G"):
                    self._add_matchup("7", serie)
                if (serie["seriesCode"] == "H"):
                    self._add_matchup("8", serie)

                # Round 2
                if (serie["seriesCode"] == "I"):
                    self._add_new_matchup("9", "1", "2")
                if (serie["seriesCode"] == "J"):
                    self._add_new_matchup("10", "3", "4")
                if (serie["seriesCode"] == "K"):
                    self._add_new_matchup("11", "5", "6")
                if (serie["seriesCode"] == "L"):
                    self._add_new_matchup("12", "7", "8")

                # Round 3, Semi/Conference final
                if (serie["seriesCode"] == "M"):
                    self._add_new_matchup("13", "9", "10")
                if (serie["seriesCode"] == "N"):
                    self._add_new_matchup("14", "11", "12")

                # Round 4, Stanley Cup final
                if (serie["seriesCode"] == "O"):
                    self._add_new_matchup("15", "13", "14")

            # Insert teams into bracket
            for matchup in self.matchups:
                self._insert_team_to_bracket(
                    matchup["teams"]["top"], matchup["location"]["top"])
                self._insert_team_to_bracket(
                    matchup["teams"]["bottom"], matchup["location"]["bottom"])

                if (matchup["id"] == "15"):
                    textLocX = 665
                    textLocY = 560
                else:
                    textLocX = matchup["location"]["top"][0] + 70
                    textLocY = int((matchup["location"]["top"]
                                    [1] + matchup["location"]["bottom"][1] + 90) / 2)

                self._insert_status_to_bracket(
                    matchup["status"], (textLocX, textLocY))

            # Create in-memory image
            file = BytesIO()
            self.BRACKET_IMG.save(file, "PNG")
            file.seek(0)
            if (self.saveImg):
                file.name = f"{self.season}.png"
                img = Image.open(file)
                img.save(file.name)
            return file
        except Exception:
            logger.exception("Error getting playoff bracket")

    def _add_matchup(self, id: str, serie: dict):
        self.matchups.append({
            "id": id,
            "location": self.LOGO_LOCATIONS[id],
            "teams": self._get_serie_teams(serie),
            "status": self._get_serie_status(serie),
            "winner": self._get_serie_winner(serie)
        })

    def _add_new_matchup(self, id: str, matchupA: str, matchupB: str):
        teamA = self._find_matchup_winner(matchupA)
        teamB = self._find_matchup_winner(matchupB)
        serie = self._find_serie_by_teams([teamA, teamB])
        self._add_matchup(id, serie)

    def _get_serie_teams(self, serie: dict):
        teams = [team for team in serie["matchupTeams"]]
        topTeam = next(team["team"]["name"]
                       for team in teams if team["seed"]["isTop"])
        bottomTeam = next(team["team"]["name"]
                          for team in teams if not team["seed"]["isTop"])
        return {
            "top": self.teams[topTeam]["shortName"],
            "bottom": self.teams[bottomTeam]["shortName"]
        }

    def _get_serie_status(self, serie: dict):
        return serie["currentGame"]["seriesSummary"]["seriesStatusShort"]

    def _get_serie_winner(self, serie: dict):
        teams = [team for team in serie["matchupTeams"]]
        for team in teams:
            if team["seriesRecord"]["wins"] == 4:
                return self.teams[team["team"]["name"]]["shortName"]

    def _find_serie_by_teams(self, teams: list):
        series = [serie for serie in self.series]
        return next(serie for serie in series
                    if set([serie["names"]["teamAbbreviationA"],
                            serie["names"]["teamAbbreviationB"]]) == set(teams))

    def _find_matchup_winner(self, id: str):
        return next(matchup["winner"] for matchup in self.matchups if matchup["id"] == id)

    def _insert_team_to_bracket(self, team: str, location: tuple):
        teamImg = Image.open(f"static/NHL_logos/{team}.gif")
        width, height = teamImg.size
        teamImg = teamImg.resize((int(0.9 * width), int(0.9 * height)))
        self.BRACKET_IMG.paste(teamImg, location)

    def _insert_status_to_bracket(self, status: str, location: tuple):
        font = ImageFont.truetype(self.BRACKET_FONT, 22)
        textImg = ImageDraw.Draw(self.BRACKET_IMG)
        textImg.text(location, status, anchor="mm",
                     font=font, fill=(0, 0, 0))
