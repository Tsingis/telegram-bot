import unittest
from io import BytesIO
from ddt import ddt, data
from src.command import Command


@ddt
class TestCommand(unittest.TestCase):
    @data(
        "/bot",
        "/weather Tampere",
        "/f1results",
        "/f1standings",
        "/f1race",
        "/nhlscoring",
        "/nhlscoring TBL",
        "/nhlscoring 15 FIN",
        "/nhlcontract connor mcdavid",
        "/nhlcontract andrei vasilevskiy",
    )
    def test_valid_command(self, text, print_response=True):
        cmd = Command(text)
        res = cmd.response

        if print_response:
            self._print_response(res, text)

        if res.text is not None:
            self.assertIsInstance(res.text, str)
            self.assertNotEqual(res.text, "")

        if res.image is not None:
            if isinstance(res.image, str):
                self.assertTrue(res.image.startswith("http"))
            else:
                self.assertIsInstance(res.image, BytesIO)

    @data("/notacommand", "notacommand", "", None)
    def test_invalid_command(self, text):
        cmd = Command(text)
        self.assertIsNone(cmd.response)

    def _print_response(self, res, command_text):
        print(f"COMMAND: {command_text}\n")
        if res.text is not None:
            print(res.text)
        if res.image is not None:
            print(res.image)
        print("\n\n")


if __name__ == "__main__":
    unittest.main()
