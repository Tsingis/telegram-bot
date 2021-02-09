import unittest


if __name__ == '__main__':
    tests = unittest.TestLoader().discover('.', '*Test.py')
    runner = unittest.TextTestRunner()
    result = runner.run(tests)
