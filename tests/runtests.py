import unittest


if __name__ == "__main__":
    tests = unittest.TestLoader().discover(".", "*test.py")
    runner = unittest.TextTestRunner()
    result = runner.run(tests)
