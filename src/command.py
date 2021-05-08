from enum import Enum
from .services.formulaoneadvanced import FormulaOneAdvanced
from .services.imagesearch import ImageSearch
from .services.weathersearch import WeatherSearch
from .services.nhladvanced import NHLAdvanced
from .services.nhlextra import NHLExtra
from .logger import logging


logger = logging.getLogger(__name__)


class ResponseType(Enum):
    TEXT = 1,
    IMAGE = 2
    TEXT_AND_IMAGE = 3


class Response():
    def __init__(self, text=None, image=None, type=ResponseType.TEXT):
        self.text = text
        self.image = image
        self.type = type


class Command():
    AVAILABLE_CMD = "/bot"
    IMAGE_SEARCH_CMD = "/search"
    WEATHER_SEARCH_CMD = "/weather"
    F1_INFO_CMD = "/f1info"
    F1_STANDINGS_CMD = "/f1standings"
    F1_RESULTS_CMD = "/f1results"
    NHL_INFO_CMD = "/nhlinfo"
    NHL_STANDINGS_CMD = "/nhlstandings"
    NHL_RESULTS_CMD = "/nhlresults"
    NHL_PLAYERS_STATS_CMD = "/nhlplayers"
    NHL_PLAYER_INFO_CMD = "/nhlplayerinfo"
    NHL_PLAYOFFS_CMD = "/nhlplayoffs"

    def __init__(self, text):
        self.text = text
        self.imgSearch = None
        self.weatherSearch = None
        self.nhlAdvanced = None
        self.nhlExtra = None
        self.f1Advanced = None

    def commandDisabled(self):
        return Response(text="Command is disabled")

    def response(self):
        if (self.text.startswith("/nhl")):
            self.nhlAdvanced = NHLAdvanced()
            self.nhlExtra = NHLExtra()
        if (self.text.startswith("/f1")):
            self.f1Advanced = FormulaOneAdvanced()

        if (self.text.startswith(self.AVAILABLE_CMD)):
            return self.available_commands()
        if (self.text.startswith(self.IMAGE_SEARCH_CMD)):
            self.imgSearch = ImageSearch()
            return self.search_img()
        if (self.text.startswith(self.WEATHER_SEARCH_CMD)):
            self.weatherSearch = WeatherSearch()
            return self.search_weather()
        if (self.text.startswith(self.F1_INFO_CMD)):
            return self.f1_info()
        if (self.text.startswith(self.F1_STANDINGS_CMD)):
            return self.f1_standings()
        if (self.text.startswith(self.F1_RESULTS_CMD)):
            return self.f1_results()
        if (self.text.startswith(self.NHL_INFO_CMD)):
            return self.nhl_info()
        if (self.text.startswith(self.NHL_STANDINGS_CMD)):
            return self.nhl_standings()
        if (self.text.startswith(self.NHL_RESULTS_CMD)):
            return self.nhl_results()
        if (self.text.startswith(self.NHL_PLAYERS_STATS_CMD)):
            return self.nhl_players_stats()
        if (self.text.startswith(self.NHL_PLAYER_INFO_CMD)):
            return self.nhl_player_info()
        if (self.text.startswith(self.NHL_PLAYOFFS_CMD)):
            return self.nhl_playoffs()
        else:
            logging.info(f"Invalid command received: {self.text}")

    # Available bot commands
    def available_commands(self):
        header = "*Available commands:*\n"
        cmds = [
            self.IMAGE_SEARCH_CMD + " <keyword>",
            self.WEATHER_SEARCH_CMD + " <location>",
            self.F1_INFO_CMD,
            self.F1_STANDINGS_CMD + " <'driver'> or <'team'>",
            self.F1_RESULTS_CMD,
            self.NHL_INFO_CMD,
            self.NHL_STANDINGS_CMD,
            self.NHL_RESULTS_CMD,
            self.NHL_PLAYERS_STATS_CMD + " <nationality> or <team>",
            self.NHL_PLAYER_INFO_CMD + " <player name>",
            self.NHL_PLAYOFFS_CMD
        ]
        return Response(text=header + "\n".join(cmds))

    # Random Google search image by keyword
    def search_img(self):
        keyword = self.text.split(self.IMAGE_SEARCH_CMD)[-1].strip()
        img = self.imgSearch.search_random_image(keyword)
        if (img is not None):
            return Response(image=img, type=ResponseType.IMAGE)
        else:
            return Response(text="No search results")

    # Weather info by location
    def search_weather(self):
        location = self.text.split(self.WEATHER_SEARCH_CMD)[-1].strip()
        info = self.weatherSearch.get_info(location)
        if (info is not None):
            result = self.weatherSearch.format_info(info, location)
            icon = self.weatherSearch.get_icon_url(info)
            if (icon is not None):
                return Response(text=result, image=icon, type=ResponseType.TEXT_AND_IMAGE)
        else:
            result = "Weather data not available"
        return Response(text=result)

    # F1 upcoming race
    def f1_info(self):
        info = self.f1Advanced.get_upcoming()
        if (info is not None):
            result = self.f1Advanced.format_upcoming(info)
            circuitImg = self.f1Advanced.find_circuit_image(info["raceUrl"])
            if (circuitImg is not None):
                return Response(text=result, image=circuitImg, type=ResponseType.TEXT_AND_IMAGE)
        else:
            result = "Race info not available"
        return Response(text=result)

    # F1 standings
    def f1_standings(self):
        parameter = self.text.split(self.F1_STANDINGS_CMD)[-1].strip().upper()
        if (parameter == "TEAM"):
            standings = self.f1Advanced.get_team_standings(amount=10)
        else:
            standings = self.f1Advanced.get_driver_standings(amount=10)
        result = self.f1Advanced.format_standings(
            standings) if standings is not None else "Standings not available"
        return Response(text=result)

    # F1 latest race results
    def f1_results(self):
        results = self.f1Advanced.get_results()
        result = self.f1Advanced.format_results(
            results) if results is not None else "Results not available"
        return Response(text=result)

    # NHL upcoming matches
    def nhl_info(self):
        info = self.nhlAdvanced.get_upcoming()
        if (info is not None):
            result = f"*Upcoming matches:*\n{self.nhlAdvanced.format_upcoming(info)}"
        else:
            result = "No upcoming games tomorrow"
        return Response(text=result)

    # NHL standings
    def nhl_standings(self):
        url = "https://www.nhl.com/standings/"
        standings = self.nhlAdvanced.get_standings()
        if (standings is not None):
            result = self.nhlAdvanced.format_standings(
                standings) + f"\n[Details]({url})"
        else:
            result = "Standings not available"
        return Response(text=result)

    # NHL latest match results
    def nhl_results(self):
        url = "https://www.livetulokset.com/jaakiekko/"
        results = self.nhlAdvanced.get_results()
        if (results is not None):
            result = f"*Results:*\n{self.nhlAdvanced.format_results(results)}\n[Details]({url})"
        else:
            result = "No matches yesterday"
        return Response(text=result)

    # NHL stats for players of given nationality or team from latest round
    def nhl_players_stats(self):
        filter = self.text.split(
            self.NHL_PLAYERS_STATS_CMD)[-1].strip().upper()
        stats = self.nhlAdvanced.get_players_stats()
        if (stats is not None):
            if (not filter):
                result = self.nhlAdvanced.format_players_stats(stats)
            else:
                result = self.nhlAdvanced.format_players_stats(stats, filter)
        else:
            result = "Players stats not available"
        return Response(text=result)

    # NHL player stats by player name
    def nhl_player_info(self):
        playerName = self.text.split(
            self.NHL_PLAYER_INFO_CMD)[-1].strip().lower()
        stats = self.nhlAdvanced.get_player_stats(playerName)
        contract = self.nhlExtra.get_player_contract(playerName)
        result = ""
        if (stats is not None):
            result += self.nhlAdvanced.format_player_stats(stats)
        if (contract is not None):
            result += "\n" + self.nhlExtra.format_player_contract(contract)
        if (not result):
            result += "Player info not available"
        return Response(text=result)

    # NHL playoff bracket
    def nhl_playoffs(self):
        bracketImg = self.nhlAdvanced.get_bracket()
        if (bracketImg is not None):
            return Response(image=bracketImg, type=ResponseType.IMAGE)
        else:
            return Response(text="Playoff bracket not available")
