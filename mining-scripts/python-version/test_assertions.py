import unittest
import re
import pprint
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
    TEST_REPO = "tressa_test_repo"

    @classmethod
    def setUpClass(cls):
        cls.history = mine_repo("assert", TestMineRepo.TEST_REPO, "master")
        cls.history.show()
        print()

    def setUp(self):
        print(self.id())

    def tearDown(self):
        print("{c} confident; {p} problematic; {a} apologetic".format(
            c=self.count_type("confident"), p=self.count_type("problematic"),
            a=self.count_type("apologetic")))
        print()

    def count_type(self, typename):
        count = 0
        for commit in self.expected:
            for file in commit.values():
                if file:
                    count += len_assert_lists(file[typename])
        return count

    def test_comments(self):
        """Verify proper behaviour involving comments in code"""
        self.expected = [
            {
                "comments.c": {
                    "confident": {
                        "added": set(),
                        "removed": set()
                    },
                    "problematic" : {
                        "added": set(),
                        "removed": set()
                    },
                    "apologetic": {
                        "added": {"post_comment_changes", "mid_comment_changes==1",
                            "comment_added==1", "good==not"},
                        "removed": {"post_comment_changes", "mid_comment_changes==1",
                            "comment_added==1", "good==not"}
                    }
                },
            },
            {
                "comments.c": {
                    "confident": {
                        "added": {"good==1", "good==2", "good==3", "good==4",
                            "good==5", "good==6", "good==7", "good==9",
                            "post_comment_changes", "mid_comment_changes==1",
                            "comment_added==1", "good==not"},
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
            },
        ]
        self.assertMatchedHistory()

    def test_filetypes(self):
        """Ensure that non-c files are ignored"""
        self.expected = [{}, {"longone.abc": None, "longone.c.ccc": None}]
        self.assertMatchedHistory()

    def test_basic(self):
        """Basic add/remove/change situations"""
        self.expected = [
            {
                "basic.c": {
                    "confident": {
                        "added": {"changed", "changed_surrounded",
                            "changed==b||(c!=d&&e==f)", "a==b||(c!=changed&&e==f)",
                            "extra_add1", "extra_add2",
                        },
                        "removed": {"to_delete", "to_change", "to_change_surrounded",
                            "to_change==b||(c!=d&&e==f)", "a==b||(c!=to_change&&e==f)",
                        },
                    },
                    "problematic": {
                        "added": set(),
                        "removed": set()
                    },
                    "apologetic": {
                        "added": set(),
                        "removed": set()
                    }
                }
            },
            {
                "basic.c": {
                    "confident": {
                        "added": {
                            "a", "to_delete", "c", "to_change", "d",
                            "to_change_surrounded", "f", "to_change==b||(c!=d&&e==f)",
                            "a==b||(c!=d&&e==no_change)", "a==b||(c!=to_change&&e==f)",
                            "good", "z", "x", "outside",
                        },
                        "removed": set()
                        },
                    "problematic": {
                        "added": set(),
                        "removed": set()
                    },
                    "apologetic": {
                        "added": set(),
                        "removed": set()
                    }
                },
            },
        ]
        self.assertMatchedHistory()

    def assertMatchedHistory(self):
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

        If a removed predicate contains "to_change". Then it verifies that there
        is an added "changed" assertion with same lineno.
        """
        self.assertEqual(len(self.expected), len(TestMineRepo.history.diffs))
        commits = zip(self.expected, TestMineRepo.history.diffs)
        for expect, diff in commits:
            for exp_filename, exp_contents in expect.items():
                self.assertDiffFile(diff, exp_filename, exp_contents)

        self.assert_changes()

    def assert_changes(self):
        # This is to verify efficacy of the tests
        for a in assertion_iter(TestMineRepo.history):
            if a.change == Change.removed and \
                    re.search(r".*to_change.*", a.predicate):
                changed_assertion = find_changed(a, a.parent_file)
                if not changed_assertion:
                    raise AssertionError("Could not find change for assert({p})" \
                            .format(p=a.predicate))

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


def find_changed(assertion, file):
    changed_pred = assertion.predicate.replace("to_change", "changed")
    for a in file.assertions:
        if a.predicate == changed_pred:
            return a
    return None








if __name__ == '__main__':
    unittest.main()
