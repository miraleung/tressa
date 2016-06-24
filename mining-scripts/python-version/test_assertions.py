import unittest
from assertions import *

# To run individual tests
#       (from https://docs.python.org/3.4/library/unittest.html)
# python3 -m unittest test_module1 test_module2
# python3 -m unittest test_module.TestClass
# python3 -m unittest test_module.TestClass.test_method


class TestRegex(unittest.TestCase):

    def test_match_assertions(self):
        self.assert_matches("assert", "", [])
        self.assert_matches("assert", "\n", [])
        self.assert_matches("assert", "ASSERT", [])
        self.assert_matches("assert", "assert", ["assert"])
        self.assert_matches("assert", "hi goodbye assert nice day", ["assert"])
        self.assert_matches("assert", "in 1;assert(a==b);i\n", ["assert"])
        self.assert_matches("assert",
                "assert(a==b) assert_bob 123 bob_assert assert\n",
                ["assert", "assert"])
        self.assert_matches("(assert)", "hi assert bye", ["assert"])
        self.assert_matches("assert|ASSERT|BUG_ON", "hi assert bye", ["assert"])
        self.assert_matches( "assert|ASSERT|BUG_ON",
                "hi assert bye ASSERT hi )assert(BUG_ON)",
                ["assert", "ASSERT", "assert", "BUG_ON"])
        self.assert_matches("(assert|ASSERT|BUG_ON)",
                    "hi assert bye ASSERT hi )assert(BUG_ON)",
                    ["assert", "ASSERT", "assert", "BUG_ON"])
        self.assert_matches(
                "((assert)|(ASSERT)|(BUG_ON))",
                "hi assert bye ASSERT hi )assert(BUG_ON)",
                ["assert", "ASSERT", "assert", "BUG_ON"])
        self.assert_matches( "[aA][sS][sS][Ee][Rr][Tt]|BUG_ON",
                 "hi assert bye ASSERT hi )assert(BUG_ON)",
                ["assert", "ASSERT", "assert", "BUG_ON"])

    def assert_matches(self, assertion_re, line, expected_matches):
        matches = match_assertions(assertion_re, line)
        actual_matches = [m.group() for m in matches]
        self.assertEqual(actual_matches, expected_matches)






if __name__ == '__main__':
    unittest.main()
