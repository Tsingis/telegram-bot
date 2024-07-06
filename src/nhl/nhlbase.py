import json
from datetime import datetime
from ..common.utils import convert_timezone
from ..common.logger import logging


logger = logging.getLogger(__name__)


class NHLBase:
    def __init__(self, date=datetime.now()):
        self.date_format = "%Y-%m-%d"
        self.target_timezone = "Europe/Helsinki"
        self.date = convert_timezone(dt=date, target_tz=self.target_timezone)
        year = self.date.year
        self.season = (
            f"{year - 1}{year}" if self.date.month < 9 else f"{year}{year + 1}"
        )
        with open("static/teams.json", "r") as f:
            teams = json.load(f)
            self.teams = {team["shortName"]: team["fullName"] for team in teams}
