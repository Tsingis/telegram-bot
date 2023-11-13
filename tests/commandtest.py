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
        "/f1race",
    )
    def test_bot_command(self, command_text, print_response=True):
        cmd = Command(command_text)
        res = cmd.response

        if print_response:
            self._print_response(res, command_text)

        if res.text is not None:
            self.assertIsInstance(res.text, str)
            self.assertNotEqual(res.text, "")

        if res.image is not None:
            if isinstance(res.image, str):
                self.assertTrue(res.image.startswith("http"))
            else:
                self.assertIsInstance(res.image, BytesIO)

    def _print_response(self, res, command_text):
        print(f"COMMAND: {command_text}\n")
        if res.text is not None:
            print(res.text)
        if res.image is not None:
            print(res.image)
        print("\n\n")


if __name__ == "__main__":
    unittest.main()
