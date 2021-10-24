import unittest
from ddt import ddt, data
from src.command import Command, ResponseType


@ddt
class CommandTest(unittest.TestCase):
    @data(
        "/bot",
        "/weather helsinki",
        "/search icecream",
        "/f1results",
        "/f1standings",
        "/f1info",
        "/nhlresults",
        "/nhlscoring 15",
        "/nhlstandings",
        "/nhlinfo",
        "/nhlplayers",
        "/nhlplayerinfo connor mcdavid",
        "/nhlplayoffs",
    )
    def test_bot_command(self, cmdText, printMsg=True):
        cmd = Command(cmdText)
        msg = cmd.response()
        self.assertIsNotNone(msg)
        if msg.type == ResponseType.TEXT:
            self.assertIsNotNone(msg.text)
        if msg.type == ResponseType.IMAGE:
            self.assertIsNotNone(msg.image)
        if msg.type == ResponseType.TEXT_AND_IMAGE:
            self.assertIsNotNone(msg.text)
            self.assertIsNotNone(msg.image)

        if printMsg:
            print("COMMAND: " + cmdText)
            print()
            if msg.text is not None:
                print(msg.text)
            if msg.image is not None:
                print(msg.image)
            print("\n\n")


if __name__ == "__main__":
    unittest.main()
