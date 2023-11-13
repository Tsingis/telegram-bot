from enum import Enum
from .common.logger import logging
from .common.utils import (
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

    def __init__(self, text):
        self.text = text
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
        else:
            logger.info(f"Invalid command received: {self.text}")
            return Response()

    # Available bot commands
    def _available_commands(self):
        cmds = [
            self.IMAGE_SEARCH_CMD + " <keyword>",
            self.WEATHER_SEARCH_CMD + " <location>",
            self.F1_RACE_CMD,
            self.F1_STANDINGS_CMD,
            self.F1_RESULTS_CMD,
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
        info = weather_search.get_info(location)
        if info is not None:
            text = weather_search.format_info(info, location)
            icon = weather_search.get_icon_url(info)
            if icon is not None:
                return Response(text=text, image=icon, type=ResponseType.IMAGE)
        return Response(text="No weather data available")

    # F1 upcoming race
    def _formula_race(self):
        from .formula.formularace import FormulaRace

        formula_race = FormulaRace()
        info = formula_race.get_upcoming()
        if info is not None:
            text = formula_race.format(info)
            circuit_img = formula_race.find_circuit_image(info["raceUrl"])
            if circuit_img is not None:
                return Response(text=text, image=circuit_img, type=ResponseType.IMAGE)
        return Response(text="No race info available")

    # F1 standings
    def _formula_standings(self):
        from .formula.formulastandings import FormulaStandings

        formula_standings = FormulaStandings()
        team_standings = formula_standings.get_team_standings(amount=10)
        driver_standings = formula_standings.get_driver_standings(amount=10)
        if team_standings is not None and driver_standings is not None:
            standings = team_standings | driver_standings
            text = formula_standings.format(standings)
            return Response(text=text)
        return Response(text="No standings available")

    # F1 latest race results
    def _formula_results(self):
        from .formula.formularesults import FormulaResults

        formula_results = FormulaResults()
        results = formula_results.get_results()
        if results is not None:
            text = formula_results.format(results)
            return Response(text=text)
        return Response(text="No results available")


class ResponseType(Enum):
    TEXT = 1
    IMAGE = 2


class Response:
    def __init__(self, text=None, image=None, type=ResponseType.TEXT):
        self.text = text
        self.image = image
        self.type = type
