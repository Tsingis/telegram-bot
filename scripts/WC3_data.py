import datetime as dt

from scripts.common_helper import set_soup, format_markdown


def get_events():
    # Set soup
    soup = set_soup("https://www.back2warcraft.com/")
    try:
        # Get data for streamed events
        data = soup.find("div", {"class": "list-events"})

        # Get event names
        names = [format_markdown(name.find("h2").text.strip()) for name in data.find_all("div", {"class": "event-description"})]

        # Get event urls
        urls = ["".join([url["href"] for url in text.find_all("a")]) for text in data.find_all("div", {"class": "event-descriptiontext"})]

        # Get event info such as casters, time and prize pools for each stream
        info = [[info.text for info in event.find_all("span")] for event in data.find_all("div", {"class": "event-infos"})]
        casters = [value[3] for value in info]
        times = [value[1] for value in info]

        # Get event dates
        dates = [" ".join([value.text for value in dates.find_all("span")]) for dates in data.find_all("div", {"class": "event-date"})]

        # Format starting datetimes into Finnish time
        datetimes = [f"{date} {time}" for time, date in zip(times, dates)]
        datetimes = [(dt.datetime.strptime(value, "%d %b %y %H:%M CET") + dt.timedelta(hours=1)).strftime("%H:%M on %b %d") for value in datetimes]

        # Format results
        return [f"{names[event]}\nStarting {datetimes[event]}\nCasting: {casters[event]}\n[Details]({urls[event]})\n" for event in range(len(names))]
    except Exception:
        return None
