from enum import Enum
from .common.logger import logging
from .common.utils import (
    find_first_integer,
    find_first_word,
    format_as_header,
    escape_special_chars,
)

logger = logging.getLogger(__name__)


class Command:
    AVAILABLE_CMD = "/bot"
    IMAGE_SEARCH_CMD = "/search"
    WEATHER_SEARCH_CMD = "/weather"
    F1_RACE_CMD = "/f1race"
    F1_STANDINGS_CMD = "/f1standings"
    F1_RESULTS_CMD = "/f1results"
    NHL_SCORING_CMD = "/nhlscoring"
    NHL_CONTRACT_CMD = "/nhlcontract"

    def __init__(self, text):
        self.text = text if text is not None else ""
        self.response = self._command_response()

    def _command_response(self):
        if self.text.startswith(self.AVAILABLE_CMD):
            return self._available_commands()
        if self.text.startswith(self.IMAGE_SEARCH_CMD):
            return self._search_img()
        if self.text.startswith(self.WEATHER_SEARCH_CMD):
            return self._search_weather()
        if self.text.startswith(self.F1_RACE_CMD):
            return self._formula_race()
        if self.text.startswith(self.F1_STANDINGS_CMD):
            return self._formula_standings()
        if self.text.startswith(self.F1_RESULTS_CMD):
            return self._formula_results()
        if self.text.startswith(self.NHL_SCORING_CMD):
            return self._nhl_scoring()
        if self.text.startswith(self.NHL_CONTRACT_CMD):
            return self._nhl_contract()
        return None

    # Available bot commands
    def _available_commands(self):
        cmds = [
            self.IMAGE_SEARCH_CMD + " <keyword>",
            self.WEATHER_SEARCH_CMD + " <location>",
            self.F1_RACE_CMD,
            self.F1_STANDINGS_CMD,
            self.F1_RESULTS_CMD,
            self.NHL_SCORING_CMD + " <amount> and/or <nationality>",
            self.NHL_CONTRACT_CMD + " <player name>",
        ]
        header = format_as_header("Available commands:")
        text = header + "\n" + escape_special_chars("\n".join(cmds))
        return Response(text=text)

    # Random Google search image by keyword
    def _search_img(self):
        from .other.imagesearch import ImageSearch

        img_search = ImageSearch()
        keyword = self.text.split(self.IMAGE_SEARCH_CMD)[-1].strip()
        img = img_search.get_random_image(keyword)
        if img is not None:
            return Response(image=img, type=ResponseType.IMAGE)
        return Response(text="No search results available")

    # Weather info by location
    def _search_weather(self):
        from .other.weathersearch import WeatherSearch

        weather_search = WeatherSearch()
        location = self.text.split(self.WEATHER_SEARCH_CMD)[-1].strip()
        data = weather_search.get_info(location)
        if data is not None:
            text = weather_search.format_info(data, location)
            icon = weather_search.get_icon_url(data)
            if icon is not None:
                return Response(text=text, image=icon, type=ResponseType.IMAGE)
        return Response(text="No weather data available")

    # F1 upcoming race
    def _formula_race(self):
        from .formula.formularace import FormulaRace

        formula_race = FormulaRace()
        data = formula_race.get_upcoming()
        if data is not None:
            text = formula_race.format(data)
            circuit_img = formula_race.find_circuit_image(data["raceUrl"])
            if circuit_img is not None:
                return Response(text=text, image=circuit_img, type=ResponseType.IMAGE)
        return Response(text="No race info available")

    # F1 standings
    def _formula_standings(self):
        from .formula.formulastandings import FormulaStandings

        formula_standings = FormulaStandings()
        team_data = formula_standings.get_team_standings(amount=10)
        driver_data = formula_standings.get_driver_standings(amount=10)
        if (
            team_data is not None
            and team_data["teamStandings"]
            and driver_data is not None
            and driver_data["driverStandings"]
        ):
            data = team_data | driver_data
            text = formula_standings.format(data)
            return Response(text=text)
        return Response(text="No standings available")

    # F1 latest race results
    def _formula_results(self):
        from .formula.formularesults import FormulaResults

        formula_results = FormulaResults()
        data = formula_results.get_results()
        if data is not None and data["results"]:
            text = formula_results.format(data)
            return Response(text=text)
        return Response(text="No results available")

    def _nhl_scoring(self):
        from .nhl.nhlscoring import NHLScoring

        nhl_scoring = NHLScoring()
        filters = self.text.split(self.NHL_SCORING_CMD)[-1].strip().split(" ")
        team_or_nationality = find_first_word(filters)
        amount = find_first_integer(filters)
        amount = 10 if amount is None else amount
        data = nhl_scoring.get_scoring_leaders(amount, team_or_nationality)
        if data is not None:
            text = nhl_scoring.format(data)
            return Response(text=text)
        return Response(text="No scoring leaders available")

    def _nhl_contract(self):
        from .nhl.nhlcontract import NHLContract

        nhl_contract = NHLContract()
        player_name = self.text.split(self.NHL_CONTRACT_CMD)[-1].strip().lower()
        data = nhl_contract.get(player_name)
        if data is not None:
            text = nhl_contract.format(player_name, data)
            return Response(text=text)
        return Response(text="No contract available")


class ResponseType(Enum):
    TEXT = 1
    IMAGE = 2


class Response:
    def __init__(self, text=None, image=None, type=ResponseType.TEXT):
        self.text = text
        self.image = image
        self.type = type
