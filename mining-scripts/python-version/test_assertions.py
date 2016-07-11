import unittest
import re
from assertions import *

# To run all tests:
# python3 test_assertions.py

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

    def test_strip_parens(self):
        self.assertEqual(strip_parens("   (abc)   "), "abc")
        self.assertEqual(strip_parens("(abc)   "), "abc")
        self.assertEqual(strip_parens("(abc)"), "abc")
        self.assertEqual(strip_parens("   (abc)"), "abc")
        self.assertEqual(strip_parens("((abc))"), "(abc)")

        with self.assertRaises(Exception):
            strip_parens("abc")
        with self.assertRaises(Exception):
            strip_parens("abc)")
        with self.assertRaises(Exception):
            strip_parens("(abc")
        with self.assertRaises(Exception):
            strip_parens("a(b)c")


class TestMineRepo(unittest.TestCase):
    TEST_REPO = "test_repo"

    """Any files that are listed in each of the ordered revisions should
    contain what's listed. Order of revisions is latest first. "apologetic"
    are 'confident' assertions that shouldn't exist, but that are expected.
    """
    EXPECTED = [
            {
                "diverse.c": {
                    "confident": {
                        "added": {"good==1", "good==2", "good==3", "good==4",
                            "good==5", "good==6", "good==7", "good==9"},
                        "removed": set()
                    },
                    "problematic" : {
                        "added": {"maybe==1"},
                        "removed": set()
                    },
                    "apologetic": {
                        "added": {"bad==5", "bad==8", "bad==9"},
                        "removed": set()
                    }
                },
                "longone.abc": None,
                "longone.c.ccc": None
            }
        ]

    def setUp(self):
        self.history = mine_repo("assert", self.TEST_REPO, "master")

    def tearDown(self):
        self.history.show()
        print("\nNumber of apologetic matches: {num}".format(
            num=self.count_apologetics()))

    def count_apologetics(self):
        count = 0
        for commit in self.EXPECTED:
            for file in commit.values():
                if file:
                    count += len_assert_lists(file["apologetic"])
        return count

    def test_comment_DIFFIculties(self):
        self.assertMatchedHistory(self.history, self.EXPECTED)

    def assertMatchedHistory(self, history, expectation):
        """Assuming there are the same number of commits in history as in
        expectation, checks that the given predicates are the only ones in
        History. It ignores files that are not included in Expectation for
        a commit, but if you want to verify that a file is NOT present, set
        its dict to None.
        A file's dict consists of three parts:
            "confident": the good assertions that are in the .assertions field
            "apologetic": the bad assertions that are regrettably undectabley
                bad, so appear in .assertions field.
            "problematic": the problematic assertions that are picked up.
        There can be no whitespace in predicates.
        """
        commits = zip(history.diffs, expectation)
        for diff, expect in commits:
            for exp_filename, exp_contents in expect.items():
                self.assertDiffFile(diff, exp_filename, exp_contents)

    def assertDiffFile(self, diff, exp_filename, exp_contents):
        act_filenames = [f.name for f in diff.files]
        if exp_contents is None:
            self.assertNotIn(exp_filename, act_filenames)
            return

        self.assertIn(exp_filename, act_filenames)

        file = find_file(exp_filename, diff.files)
        self.assertExpectedAsserts(file, exp_contents)

        # Since everything was converted to a set, this confirms that
        # there were no duplicates
        self.assertEqual(len_confident(exp_contents), len(file.assertions))


    def assertExpectedAsserts(self, file, exp_contents):
        """Check that all asserts in exp_contents are present as indicated.
        Verify that nothing else is included also.
        """
        # .assertions
        exp_addeds = exp_contents["confident"]["added"].union(
                    exp_contents["apologetic"]["added"])
        exp_removeds = exp_contents["confident"]["removed"].union(
                    exp_contents["apologetic"]["removed"])

        act_addeds = {remove_whitespace(a.predicate) for a in file.assertions
                if a.change is Change.added}
        act_removeds = {remove_whitespace(a.predicate) for a in file.assertions
                if a.change is Change.removed}

        self.assertSetEqual(act_addeds, exp_addeds)
        self.assertSetEqual(act_removeds, exp_removeds)

        # .to_inspect
        exp_addeds = exp_contents["problematic"]["added"]
        exp_removeds = exp_contents["problematic"]["removed"]

        act_addeds = {remove_whitespace(" ".join(a.raw_lines)) for a in file.to_inspect
                if a.change is Change.added}
        act_removeds = {remove_whitespace(" ".join(a.raw_lines)) for a in file.to_inspect
                if a.change is Change.removed}

        for pred in exp_addeds:
            self.assertMatchDelete(pred, act_addeds)

        for pred in exp_removeds:
            self.assertMatchDelete(pred, act_removeds)

        self.assertSetEqual(set(), act_addeds)
        self.assertSetEqual(set(), act_removeds)

    def assertMatchDelete(self, pred, assert_lines):
        # TODO: This is brittle; requires enough of the assert to have been added
        # to predicate, and that the assert is 'assert' (the latter could
        # easily be removed, however
        match = None
        for l in assert_lines:
            print(l)
            match = re.search(r"assert\({p}\)".format(p=re.escape(pred)), l)
            if match:
                break
        if match:
            assert_lines.remove(match.string)
        else:
            raise AssertionError("Problematic predicate not found: " + pred)








# string [File] -> File
def find_file(filename, files):
    for file in files:
        if filename == file.name:
            return file
    raise AssertionError("file not found: " + filename)


def len_confident(file_expects):
    confident = file_expects["confident"]
    apologetic = file_expects["apologetic"]
    return len_assert_lists(confident) + len_assert_lists(apologetic)


def len_assert_lists(assert_list):
    return len(assert_list["added"]) + len(assert_list["removed"])











        # self.assertEqual(num_asserts(self.hist), 8)
        # self.assertEqual(num_file_asserts("diverse.c", self.history), 8)

        # diff = self.history.diffs[-1]
        # self.assertEqual(len(diff.files), 1)

        # file = diff.files[-1]
        # self.assertEqual(file.name, "diverse.c")
        # self.assertEqual(num_confident(file), 8)
        # self.assertEqual(num_problematic(file), 2)





# def num_asserts(history):
    # """Return the number of assert statements of predicate (good==X) found
    # among both confident and problematic in entire history.
    # """
    # return 0

# def num_file_asserts(filepath, history):
    # """In given history, all the assertions found in the given file
    # throughout all diffs."""
    # return 0

# def num_confident(file):
    # """For given File object, the number of confident assertions found."""
    # return 0

# def num_problematic(file):
    # """For given File object, the number of confident assertions found."""
    # return 0













if __name__ == '__main__':
    unittest.main()
