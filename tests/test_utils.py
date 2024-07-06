import unittest
from datetime import datetime
from ddt import ddt, data, unpack
from src.common.utils import (
    find_first_integer,
    find_first_word,
    convert_timezone,
    text_to_datetime,
    datetime_to_text,
)


@ddt
class TestUtils(unittest.TestCase):
    @data(
        ([], None),
        (["123"], 123),
        (["abc", "123"], 123),
        (["0", "123"], 0),
        (["abc", "-1"], -1),
        (["abc", "1.23"], None),
        (["1.23", "123"], 123),
        (["123abc", "abc"], None),
    )
    @unpack
    def test_find_first_integer(self, texts, expected):
        result = find_first_integer(texts)
        self.assertEqual(result, expected)

    @data(
        ([], None),
        (["123"], None),
        (["abc", "123"], "abc"),
        (["-", "abc"], "abc"),
        (["abc", "1.23"], "abc"),
        (["1.23", "123"], None),
    )
    @unpack
    def test_find_first_word(self, texts, expected):
        result = find_first_word(texts)
        self.assertEqual(result, expected)

    @data(
        (None, None, 12),
        ("UTC", "UTC", 12),
        ("Europe/Helsinki", "UTC", 9),
        ("UTC", "Europe/Helsinki", 15),
    )
    @unpack
    def test_convert_timezone_EEST(self, source_tz, target_tz, expected_hour):
        dt = datetime(2010, 10, 10, 12, 12, 12)
        result = convert_timezone(dt, source_tz, target_tz)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.hour, expected_hour)

    @data(
        (None, None, 12),
        ("UTC", "UTC", 12),
        ("Europe/Helsinki", "UTC", 10),
        ("UTC", "Europe/Helsinki", 14),
    )
    @unpack
    def test_convert_timezone_EET(self, source_tz, target_tz, expected_hour):
        dt = datetime(2010, 11, 10, 12, 12, 12)
        result = convert_timezone(dt, source_tz, target_tz)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.hour, expected_hour)

    def test_text_to_datetime(self):
        text = "2010-10-10 12:12:12"
        pattern = "%Y-%m-%d %H:%M:%S"
        result = text_to_datetime(text, pattern)
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2010)
        self.assertEqual(result.month, 10)
        self.assertEqual(result.day, 10)
        self.assertEqual(result.hour, 12)
        self.assertEqual(result.minute, 12)
        self.assertEqual(result.second, 12)
        self.assertIsNone(result.tzinfo)

    def test_datetime_to_text(self):
        dt = datetime(2010, 10, 10, 12, 12, 12, 123000)
        pattern = "%Y-%m-%d %H:%M:%S.%f"
        result = datetime_to_text(dt, pattern)
        self.assertIsInstance(result, str)
        self.assertEqual(result, "2010-10-10 12:12:12.123000")


if __name__ == "__main__":
    unittest.main()
