from enum import Enum
from .services.formula.formulaoneadvanced import FormulaOneAdvanced
from .services.other.imagesearch import ImageSearch
from .services.other.weathersearch import WeatherSearch
from .services.nhl.nhladvanced import NHLAdvanced
from .services.nhl.nhlextra import NHLExtra
from .services.nhl.nhlplayoffs import NHLPlayoffs
from .services.nhl.nhlformatter import NHLFormatter
from .logger import logging


logger = logging.getLogger(__name__)


class ResponseType(Enum):
    TEXT = 1
    IMAGE = 2
    TEXT_AND_IMAGE = 3


class Response:
    def __init__(self, text=None, image=None, type=ResponseType.TEXT):
        self.text = text
        self.image = image
        self.type = type


class Command:
    AVAILABLE_CMD = "/bot"
    IMAGE_SEARCH_CMD = "/search"
    WEATHER_SEARCH_CMD = "/weather"
    F1_INFO_CMD = "/f1info"
    F1_STANDINGS_CMD = "/f1standings"
    F1_RESULTS_CMD = "/f1results"
    NHL_INFO_CMD = "/nhlinfo"
    NHL_STANDINGS_CMD = "/nhlstandings"
    NHL_RESULTS_CMD = "/nhlresults"
    NHL_SCORING_CMD = "/nhlscoring"
    NHL_PLAYERS_STATS_CMD = "/nhlplayers"
    NHL_PLAYER_INFO_CMD = "/nhlplayerinfo"
    NHL_PLAYOFFS_CMD = "/nhlplayoffs"

    def __init__(self, text):
        self.text = text
        if self.text.startswith(self.IMAGE_SEARCH_CMD):
            self.img_search = ImageSearch()
        if self.text.startswith(self.WEATHER_SEARCH_CMD):
            self.weather_search = WeatherSearch()
        if self.text.startswith("/nhl"):
            self.nhl_advanced = NHLAdvanced()
            self.nhl_extra = NHLExtra()
            self.nhl_playoffs = NHLPlayoffs()
            self.nhl_formatter = NHLFormatter()
        if self.text.startswith("/f1"):
            self.f1_advanced = FormulaOneAdvanced()
        self.response = self._command_response()

    def _command_response(self):
        if self.text.startswith(self.AVAILABLE_CMD):
            return self._available_commands()
        if self.text.startswith(self.IMAGE_SEARCH_CMD):
            return self._search_img()
        if self.text.startswith(self.WEATHER_SEARCH_CMD):
            return self._search_weather()
        if self.text.startswith(self.F1_INFO_CMD):
            return self._f1_info()
        if self.text.startswith(self.F1_STANDINGS_CMD):
            return self._f1_standings()
        if self.text.startswith(self.F1_RESULTS_CMD):
            return self._f1_results()
        if self.text.startswith(self.NHL_SCORING_CMD):
            return self._nhl_scoring()
        if self.text.startswith(self.NHL_INFO_CMD):
            return self._nhl_info()
        if self.text.startswith(self.NHL_STANDINGS_CMD):
            return self._nhl_standings()
        if self.text.startswith(self.NHL_RESULTS_CMD):
            return self._nhl_results()
        if self.text.startswith(self.NHL_PLAYERS_STATS_CMD):
            return self._nhl_players_stats()
        if self.text.startswith(self.NHL_PLAYER_INFO_CMD):
            return self._nhl_player_info()
        if self.text.startswith(self.NHL_PLAYOFFS_CMD):
            return self._nhl_playoffs_bracket()
        else:
            logging.info(f"Invalid command received: {self.text}")

    # Available bot commands
    def _available_commands(self):
        header = "*Available commands:*\n"
        cmds = [
            self.IMAGE_SEARCH_CMD + " <keyword>",
            self.WEATHER_SEARCH_CMD + " <location>",
            self.F1_INFO_CMD,
            self.F1_STANDINGS_CMD,
            self.F1_RESULTS_CMD,
            self.NHL_INFO_CMD,
            self.NHL_STANDINGS_CMD,
            self.NHL_RESULTS_CMD,
            self.NHL_SCORING_CMD + " <amount>",
            self.NHL_PLAYERS_STATS_CMD + " <nationality> or <team>",
            self.NHL_PLAYER_INFO_CMD + " <player name>",
            self.NHL_PLAYOFFS_CMD,
        ]
        return Response(text=header + "\n".join(cmds))

    # Random Google search image by keyword
    def _search_img(self):
        keyword = self.text.split(self.IMAGE_SEARCH_CMD)[-1].strip()
        img = self.img_search.search_random_image(keyword)
        if img is not None:
            return Response(image=img, type=ResponseType.IMAGE)
        return Response(text="No search results")

    # Weather info by location
    def _search_weather(self):
        text = "Weather data not available"
        location = self.text.split(self.WEATHER_SEARCH_CMD)[-1].strip()
        info = self.weather_search.get_info(location)
        if info is not None:
            text = self.weather_search.format_info(info, location)
            icon = self.weather_search.get_icon_url(info)
            if icon is not None:
                return Response(text=text, image=icon, type=ResponseType.TEXT_AND_IMAGE)
        return Response(text=text)

    # F1 upcoming race
    def _f1_info(self):
        text = "Race info not available"
        info = self.f1_advanced.get_upcoming()
        if info is not None:
            text = self.f1_advanced.format_upcoming(info)
            circuit_img = self.f1_advanced.find_circuit_image(info["raceUrl"])
            if circuit_img is not None:
                return Response(
                    text=text, image=circuit_img, type=ResponseType.TEXT_AND_IMAGE
                )
        return Response(text=text)

    # F1 standings
    def _f1_standings(self):
        text = "Standings not available"
        team_standings = self.f1_advanced.get_team_standings(amount=10)
        driver_standings = self.f1_advanced.get_driver_standings(amount=10)
        if team_standings is not None and driver_standings is not None:
            standings = team_standings | driver_standings
            text = self.f1_advanced.format_standings(standings)
        return Response(text=text)

    # F1 latest race results
    def _f1_results(self):
        text = "Results not available"
        results = self.f1_advanced.get_results()
        if results is not None:
            text = self.f1_advanced.format_results(results)
        return Response(text=text)

    # NHL upcoming matches
    def _nhl_info(self):
        text = "No upcoming games tomorrow"
        info = self.nhl_advanced.get_upcoming()
        if info is not None:
            text = f"*Upcoming matches:*\n{self.nhl_formatter.format_upcoming(info)}"
        return Response(text=text)

    # NHL standings
    def _nhl_standings(self):
        text = "Standings not available"
        url = "https://www.nhl.com/standings/"
        standings = self.nhl_advanced.get_standings()
        if standings is not None:
            text = (
                self.nhl_formatter.format_standings(standings) + f"\n[Details]({url})"
            )
        return Response(text=text)

    # NHL latest match results
    def _nhl_results(self):
        text = "No matches yesterday"
        url = "https://www.nhl.com/scores/"
        results = self.nhl_advanced.get_results()
        if results is not None:
            text = f"*Results:*\n{self.nhl_formatter.format_results(results)}\n[Details]({url})"
        return Response(text=text)

    # NHL scoring leaders
    def _nhl_scoring(self):
        text = "Scoring leaders not available"
        url = "http://www.nhl.com/stats/skaters"
        try:
            amount = int(self.text.split(self.NHL_SCORING_CMD)[-1].strip())
            if amount < 5:
                amount = 5
        except ValueError:
            logger.info(
                "Failed to parse input for scoring leaders. Using default value."
            )
            amount = 10
        info = self.nhl_extra.get_scoring_leaders(amount)
        if info is not None:
            text = (
                f"{self.nhl_formatter.format_scoring_leaders(info)}\n[Details]({url})"
            )
        return Response(text=text)

    # NHL stats for players of given nationality or team from latest round
    def _nhl_players_stats(self):
        text = "Players stats not available"
        filter_word = self.text.split(self.NHL_PLAYERS_STATS_CMD)[-1].strip().upper()
        stats = self.nhl_advanced.get_players_stats()
        if stats is not None:
            if not filter_word:
                text = self.nhl_formatter.format_players_stats(stats)
            else:
                text = self.nhl_formatter.format_players_stats(stats, filter_word)
        return Response(text=text)

    # NHL player stats by player name
    def _nhl_player_info(self):
        player_name = self.text.split(self.NHL_PLAYER_INFO_CMD)[-1].strip().lower()
        stats = self.nhl_advanced.get_player_stats(player_name)
        contract = self.nhl_extra.get_player_contract(player_name)
        text = ""
        if stats is not None:
            text += self.nhl_formatter.format_player_stats(stats)
        if contract is not None:
            text += "\n" + self.nhl_formatter.format_player_contract(contract)
        if not text:
            text = "Player info not available"
        return Response(text=text)

    # NHL playoff bracket
    def _nhl_playoffs_bracket(self):
        bracket_img = self.nhl_playoffs.get_bracket()
        if bracket_img is not None:
            return Response(image=bracket_img, type=ResponseType.IMAGE)
        return Response(text="Playoff bracket not available")
