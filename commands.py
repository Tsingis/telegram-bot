from logger import logger, OK_RESPONSE, ERROR_RESPONSE
from scripts import F1_data, NHL_data, weather_data, image_search


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
        f1_cmds = ["/f1info", "/f1results", "/f1standings"]
        nhl_cmds = ["/nhlinfo", "/nhlresults", "/nhlstandings",
                    "/nhlfinns", "/nhlplayoffs", "/nhlplayer <player name>"]
        other_cmds = ["/weather <location>", "/search <keyword>"]

        msg = ("*F1 commands:*\n" + "\n".join(f1_cmds) + "\n"
               + "*NHL commands:*\n" + "\n".join(nhl_cmds) + "\n"
               + "*Other commands:*\n" + "\n".join(other_cmds))
        send_message(msg, chat_id, bot)

    # F1 latest race results
    if (text == "/f1results"):
        url, results = F1_data.get_results()
        if (url is not None and results is not None):
            race = url.split("/")[-2].replace("-", " ").title()
            msg = f"*Results for {race}:*\n" + "\n".join(results) + f"\n[Details]({url})"
        else:
            msg = "Not available"
        send_message(msg, chat_id, bot)

    # F1 standings
    if (text == "/f1standings"):
        race_number, max_races = F1_data.get_race()
        url, standings = F1_data.get_standings()
        if (standings is not None and race_number is not None):
            msg = (f"*Standings: {(race_number - 1 if race_number < max_races else race_number)}/{max_races}*\n"
                   + "\n".join(standings) + f"\n[Details]({url})")
        else:
            msg = "Not available"
        send_message(msg, chat_id, bot)

    # # F1 upcoming race
    if (text == "/f1info"):
        info, circuit_img = F1_data.get_upcoming()
        race_number, max_races = F1_data.get_race()
        if (info is not None and circuit_img is not None and race_number is not None):
            msg = (f"*Upcoming race: {race_number}/{max_races}*\n"
                   + info["grandprix"] + "\n"
                   + info["weekend"] + " in " + info["country"] + "\n"
                   + "Qualifying at " + info["qualifying"] + "\n"
                   + "Race at " + info["race"])
            send_photo(photo=circuit_img, caption=msg, chat_id=chat_id, bot=bot)
        else:
            send_message(msg="Not available", chat_id=chat_id, bot=bot)

    # NHL latest match results
    if (text == "/nhlresults"):
        url = "https://www.livetulokset.com/jaakiekko/"
        results = NHL_data.get_results()
        if (results is not None):
            msg = "*Results:*\n" + "\n".join(results) + f"\n[Details]({url})"
        else:
            msg = "No matches yesterday"
        send_message(msg, chat_id, bot)

    # NHL standings by division
    if (text == "/nhlstandings"):
        url = "https://www.nhl.com/standings/"
        standings = NHL_data.get_standings()
        if (standings is not None):
            msg = "\n".join(standings) + f"\n[Details]({url})"
        else:
            msg = "Not available"
        send_message(msg, chat_id, bot)

    # NHL upcoming matches
    if (text == "/nhlinfo"):
        info = NHL_data.get_upcoming()
        if (info is not None):
            msg = "*Upcoming matches:*\n" + "\n".join(info)
        else:
            msg = "No upcoming games tomorrow"
        send_message(msg, chat_id, bot)

    # NHL playoff bracket
    if (text == "/nhlplayoffs"):
        bracket_img = NHL_data.create_bracket()
        if (bracket_img is not None):
            send_photo(photo=bracket_img, caption="", chat_id=chat_id, bot=bot)
        else:
            send_message(msg="Not available", chat_id=chat_id, bot=bot)

    # NHL stats for Finnish players from latest matches
    if (text == "/nhlfinns"):
        skaters, goalies = NHL_data.get_finns()
        if (skaters is not None or goalies is not None):
            if (len(skaters) > 0 and len(goalies) > 0):
                msg = "*Skaters:*\n" + "\n".join(skaters) + "\n" + "*Goalies:*\n" + "\n".join(goalies)
            elif (len(goalies) == 0 and len(skaters) > 0):
                msg = "*Skaters:*\n" + "\n".join(skaters)
            elif (len(skaters) == 0 and len(goalies) > 0):
                msg = "*Goalies:*\n" + "\n".join(goalies)
            else:
                msg = "No Finnish players yesterday"
        else:
            msg = "Not available"
        send_message(msg, chat_id, bot)

    # NHL player stats by player name
    if (text and text.startswith("/nhlplayer")):
        player_name = text.split("/nhlplayer")[-1].strip().lower()
        player_id, stats = NHL_data.get_player_stats(player_name)
        contract_url, player_contract = NHL_data.get_player_contract(player_name)
        if (stats is not None and player_id is not None):
            url = f"""https://www.nhl.com/player/{player_name.replace(" ", "-")}-{player_id}"""
            msg = stats + f"\n[Details]({url})"
            if (player_contract is not None):
                msg = msg + "\nContract:\n" + player_contract + f"\n[Details]({contract_url})"
        else:
            msg = "Not available"
        send_message(msg, chat_id, bot)

    # Weather info by location
    if (text and text.startswith("/weather")):
        location = text.split("/weather")[-1].strip()
        info = weather_data.get_data(location)
        if (info is not None):
            msg = (f"*Weather for {location.capitalize()}:*\n\n" +
                   "\n".join([f"{key}: {value}" for (key, value) in info.items()]) +
                   "\n\n *Powered by Dark Sky*")
        else:
            msg = "Not available"
        send_message(msg, chat_id, bot)

    # Random Google search image by keyword
    if (text and text.startswith("/search")):
        keyword = text.split("/search")[-1]
        photo = image_search.search_image(keyword)
        if (photo is not None):
            send_photo(photo=photo, caption="", chat_id=chat_id, bot=bot)
        else:
            send_message(msg="No results", chat_id=chat_id, bot=bot)
