from logger import logger, OK_RESPONSE, ERROR_RESPONSE
from scripts.formulaone import FormulaOne
from scripts.imagesearch import ImageSearch
from scripts.weathersearch import WeatherSearch
from scripts.nhladvanced import NHLAdvanced


f1 = FormulaOne()
img = ImageSearch()
weather = WeatherSearch()
nhl = NHLAdvanced()


def send_message(msg, chat_id, bot):
    try:
        bot.sendMessage(chat_id=chat_id, text=msg, parse_mode="Markdown",
                        disable_web_page_preview=True)
        logger.info("Message sent")
        return OK_RESPONSE
    except Exception:
        return ERROR_RESPONSE


def send_photo(photo, caption, chat_id, bot):
    try:
        bot.sendPhoto(chat_id=chat_id, photo=photo, caption=caption, parse_mode="Markdown")
        logger.info("Photo sent")
        return OK_RESPONSE
    except Exception:
        return ERROR_RESPONSE


def command_response(text, bot, chat_id):
    # Available bot commands
    if (text == "/bot"):
        f1_cmds = ["/f1info", "/f1results", "/f1standings <driver/team>"]
        nhl_cmds = ["/nhlinfo", "/nhlresults", "/nhlstandings",
                    "/nhlplayers <nationality>", "/nhlplayerinfo <player name>",
                    "/nhlplayoffs"]
        other_cmds = ["/weather <location>", "/search <keyword>"]

        msg = ("*F1 commands:*\n" + "\n".join(f1_cmds) + "\n"
               + "*NHL commands:*\n" + "\n".join(nhl_cmds) + "\n"
               + "*Other commands:*\n" + "\n".join(other_cmds))
        send_message(msg, chat_id, bot)

    # F1 latest race results
    if (text == "/f1results"):
        results = f1.get_results()
        if (results is not None):
            msg = f1.format_results(results)
        else:
            msg = "Results not available"
        send_message(msg, chat_id, bot)

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
        send_message(msg, chat_id, bot)

    # # F1 upcoming race
    if (text == "/f1info"):
        info = f1.get_upcoming()
        if (info is not None):
            circuit_img = f1.get_circuit(info["country"])
            msg = f1.format_upcoming(info)
            if (circuit_img is not None):
                send_photo(photo=circuit_img, caption=msg, chat_id=chat_id, bot=bot)
            else:
                send_message(msg, chat_id, bot)
        else:
            send_message(msg="Race info not availabe", chat_id=chat_id, bot=bot)

    # NHL latest match results
    if (text == "/nhlresults"):
        url = "https://www.livetulokset.com/jaakiekko/"
        results = nhl.get_results()
        if (results is not None):
            msg = f"*Results:*\n{nhl.format_results(results)}\n[Details]({url})"
        else:
            msg = "No matches yesterday"
        send_message(msg, chat_id, bot)

    # NHL standings by division
    if (text == "/nhlstandings"):
        url = "https://www.nhl.com/standings/"
        standings = nhl.get_standings()
        if (standings is not None):
            msg = nhl.format_standings(standings) + f"\n[Details]({url})"
        else:
            msg = "Standings not available"
        send_message(msg, chat_id, bot)

    # NHL upcoming matches
    if (text == "/nhlinfo"):
        info = nhl.get_upcoming()
        if (info is not None):
            msg = f"*Upcoming matches:*\n{nhl.format_upcoming(info)}"
        else:
            msg = "No upcoming games tomorrow"
        send_message(msg, chat_id, bot)

    # NHL playoff bracket
    if (text == "/nhlplayoffs"):
        bracket_img = nhl.create_bracket()
        if (bracket_img is not None):
            send_photo(photo=bracket_img, caption="", chat_id=chat_id, bot=bot)
        else:
            send_message(msg="Playoff bracket not available", chat_id=chat_id, bot=bot)

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
        send_message(msg, chat_id, bot)

    # NHL player stats by player name
    if (text and text.startswith("/nhlplayerinfo")):
        player_name = text.split("/nhlplayerinfo")[-1].strip().lower()
        stats = nhl.get_player_season_stats(player_name)
        contract = nhl.get_player_contract(player_name)
        if (stats is not None):
            msg = nhl.format_player_info(player_name, stats, contract)
        else:
            msg = "Player info not available"
        send_message(msg, chat_id, bot)

    # Weather info by location
    if (text and text.startswith("/weather")):
        location = text.split("/weather")[-1].strip()
        info = weather.get_data(location)
        if (info is not None):
            msg = weather.format_info(info, location)
        else:
            msg = "Weather data not available"
        send_message(msg, chat_id, bot)

    # Random Google search image by keyword
    if (text and text.startswith("/search")):
        keyword = text.split("/search")[-1].strip()
        image = img.search_random_image(keyword)
        if (image is not None):
            send_photo(photo=image, caption="", chat_id=chat_id, bot=bot)
        else:
            send_message(msg="No search results", chat_id=chat_id, bot=bot)
