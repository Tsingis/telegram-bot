import unittest
from datetime import datetime
from src.services.formula.formulaoneadvanced import FormulaOneAdvanced


class FormulaOneTest(unittest.TestCase):

    f1Advanced = FormulaOneAdvanced()

    def test_dates_are_datetime(self):
        races = self.f1Advanced.races
        for race in races:
            self.assertIsInstance(race["raceTime"], datetime)
            self.assertIsInstance(race["qualifyingTime"], datetime)

    def test_upcoming_race_exists(self):
        race = self.f1Advanced.get_upcoming()
        self.assertIsNotNone(race)


if __name__ == '__main__':
    unittest.main()
