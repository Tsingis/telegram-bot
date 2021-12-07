import unittest
from io import BytesIO
from ddt import ddt, data
from src.command import Command


@ddt
class CommandTest(unittest.TestCase):
    @data(
        "/bot",
        "/weather Tampere",
        "/search icecream",
        "/f1results",
        "/f1standings",
        "/f1info",
        "/nhlresults",
        "/nhlstandings",
        "/nhlinfo",
        "/nhlscoring 15",
        "/nhlplayers",
        "/nhlplayerinfo connor mcdavid",
        "/nhlplayerinfo andrei vasilevskiy",
        "/nhlplayoffs",
    )
    def test_bot_command(self, command_text, print_response=True):
        cmd = Command(command_text)
        res = cmd.response

        if print_response:
            self._print_response(res, command_text)

        if res.text is not None:
            text = res.text.lower()
            self.assertFalse(text.startswith("no") and "available" in text)

        if res.image is not None:
            self.assertTrue(
                isinstance(res.image, str) or isinstance(res.image, BytesIO)
            )

    def _print_response(self, res, command_text):
        print("COMMAND: " + command_text)
        print()
        if res.text is not None:
            print(res.text)
        if res.image is not None:
            print(res.image)
        print("\n\n")


if __name__ == "__main__":
    unittest.main()
