import json
import os
from datetime import datetime
from pathlib import Path
from ..common.utils import convert_timezone
from ..common.logger import logging


logger = logging.getLogger(__name__)


class NHLBase:
    def __init__(self, date=datetime.now()):
        self.date_format = "%Y-%m-%d"
        self.target_timezone = "Europe/Helsinki"
        self.date = convert_timezone(dt=date, target_tz=self.target_timezone)
        year = self.date.year
        self.season = f"{year - 1}{year}" if self.date.month < 7 else f"{year}{year + 1}"
        path = Path(__file__).resolve().parent.parent / "static"
        with open(os.path.join(path, "nhl_teams.json"), "r") as f:
            teams = json.load(f)
            self.teams = {team["shortName"]: team["fullName"] for team in teams}
