from .logger import logger, OK_RESPONSE, ERROR_RESPONSE
from .formulaone import FormulaOne
from .imagesearch import ImageSearch
from .weathersearch import WeatherSearch
from .nhladvanced import NHLAdvanced


f1 = FormulaOne()
img = ImageSearch()
weather = WeatherSearch()
nhl = NHLAdvanced()


def command_response(text, bot, chatId):
    # Available bot commands
    if (text == "/bot"):
        f1Commands = ["/f1info", "/f1results", "/f1standings <driver/team>"]
        nhlCommands = ["/nhlinfo", "/nhlresults", "/nhlstandings",
                       "/nhlplayers <nationality>", "/nhlplayerinfo <player name>",
                       "/nhlplayoffs"]
        otherCommands = ["/weather <location>", "/search <keyword>"]

        msg = ("*F1 commands:*\n" + "\n".join(f1Commands) + "\n"
               + "*NHL commands:*\n" + "\n".join(nhlCommands) + "\n"
               + "*Other commands:*\n" + "\n".join(otherCommands))
        _send_message(msg, chatId, bot)

    # F1 latest race results
    if (text == "/f1results"):
        results = f1.get_results()
        if (results is not None):
            msg = f1.format_results(results)
        else:
            msg = "Results not available"
        _send_message(msg, chatId, bot)

    # F1 standings
    if (text and text.startswith("/f1standings")):
        parameter = text.split("/f1standings")[-1].strip().upper()
        if (parameter == "TEAM"):
            standings = f1.get_team_standings(10)
        else:
            standings = f1.get_driver_standings(10)
        if (standings is not None):
            msg = f1.format_standings(standings)
        else:
            msg = "Standings not available"
        _send_message(msg, chatId, bot)

    # # F1 upcoming race
    if (text == "/f1info"):
        info = f1.get_upcoming()
        if (info is not None):
            circuitImg = f1.get_circuit(info["raceUrl"])
            msg = f1.format_upcoming(info)
            if (circuitImg is not None):
                _send_photo(photo=circuitImg, caption=msg, chatId=chatId, bot=bot)
            else:
                _send_message(msg, chatId, bot)
        else:
            _send_message(msg="Race info not availabe", chatId=chatId, bot=bot)

    # NHL latest match results
    if (text == "/nhlresults"):
        url = "https://www.livetulokset.com/jaakiekko/"
        results = nhl.get_results()
        if (results is not None):
            msg = f"*Results:*\n{nhl.format_results(results)}\n[Details]({url})"
        else:
            msg = "No matches yesterday"
        _send_message(msg, chatId, bot)

    # NHL standings by division
    if (text == "/nhlstandings"):
        url = "https://www.nhl.com/standings/"
        standings = nhl.get_standings()
        if (standings is not None):
            msg = nhl.format_standings(standings) + f"\n[Details]({url})"
        else:
            msg = "Standings not available"
        _send_message(msg, chatId, bot)

    # NHL upcoming matches
    if (text == "/nhlinfo"):
        info = nhl.get_upcoming()
        if (info is not None):
            msg = f"*Upcoming matches:*\n{nhl.format_upcoming(info)}"
        else:
            msg = "No upcoming games tomorrow"
        _send_message(msg, chatId, bot)

    # NHL playoff bracket
    if (text == "/nhlplayoffs"):
        bracketImg = nhl.create_bracket()
        if (bracketImg is not None):
            _send_photo(photo=bracketImg, caption="", chatId=chatId, bot=bot)
        else:
            _send_message(msg="Playoff bracket not available", chatId=chatId, bot=bot)

    # NHL stats for Finnish players from latest matches
    if (text and text.startswith("/nhlplayers")):
        nationality = text.split("/nhlplayers")[-1].strip().upper()
        stats = nhl.get_players_stats()
        if (stats is not None):
            if (not nationality):
                msg = nhl.format_players_stats(stats)
            else:
                msg = nhl.format_players_stats(stats, nationality)
        else:
            msg = "Players stats not available"
        _send_message(msg, chatId, bot)

    # NHL player stats by player name
    if (text and text.startswith("/nhlplayerinfo")):
        playerName = text.split("/nhlplayerinfo")[-1].strip().lower()
        stats = nhl.get_player_season_stats(playerName)
        contract = nhl.get_player_contract(playerName)
        if (stats is not None or contract is not None):
            msg = nhl.format_player_info(playerName, stats, contract)
        else:
            msg = "Player info not available"
        _send_message(msg, chatId, bot)

    # Weather info by location
    if (text and text.startswith("/weather")):
        location = text.split("/weather")[-1].strip()
        info = weather.get_data(location)
        if (info is not None):
            msg = weather.format_info(info, location)
        else:
            msg = "Weather data not available"
        _send_message(msg, chatId, bot)

    # Random Google search image by keyword
    if (text and text.startswith("/search")):
        keyword = text.split("/search")[-1].strip()
        image = img.search_random_image(keyword)
        if (image is not None):
            _send_photo(photo=image, caption="", chatId=chatId, bot=bot)
        else:
            _send_message(msg="No search results", chatId=chatId, bot=bot)


def _send_message(msg, chatId, bot):
    try:
        bot.sendMessage(chat_id=chatId, text=msg, parse_mode="Markdown",
                        disable_web_page_preview=True)
        logger.info("Message sent")
        return OK_RESPONSE
    except Exception:
        return ERROR_RESPONSE


def _send_photo(photo, caption, chatId, bot):
    try:
        bot.sendPhoto(chat_id=chatId, photo=photo, caption=caption, parse_mode="Markdown")
        logger.info("Photo sent")
        return OK_RESPONSE
    except Exception:
        return ERROR_RESPONSE
