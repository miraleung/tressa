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
        self.assert_matches("assert", "in 1;assert(a==b);\n", ["assert"])
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
        cls.test_history = history_to_testcommits(cls.history)
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
            TestCommit(
                TestFile("comments.c",
                    apologetic=TestAsserts(
                        added={"post_comment_changes", "mid_comment_changes==1",
                            "comment_added==1", "good==not"},
                        removed={"post_comment_changes", "mid_comment_changes==1",
                            "comment_added==1", "good==not"}))),
            TestCommit(
                TestFile("comments.c",
                    confident=TestAsserts(
                        added={"good==1", "good==2", "good==3", "good==4",
                            "good==5", "good==6", "good==7", "good==9",
                            "post_comment_changes", "mid_comment_changes==1",
                            "comment_added==1", "good==not"}),
                    problematic=TestAsserts(
                        added={"maybe==1"}),
                    apologetic=TestAsserts(
                        added={"bad==5", "bad==8", "bad==9"}))),
        ]
        self.assert_matching_history()

    def test_filetypes(self):
        """Ensure that non-c files are ignored"""
        self.expected = [
            TestCommit(),
            TestCommit(
                TestFile("longone.abc"),
                TestFile("longone.c.ccc"))
        ]
        self.assert_matching_history()

    def test_basic(self):
        """Basic add/remove/change situations"""
        self.expected = [
            TestCommit(
                TestFile("basic.c",
                    confident=TestAsserts(
                        added={"changed", "changed_surrounded",
                            "changed==b||(c!=d&&e==f)", "a==b||(c!=changed&&e==f)",
                            "extra_add1", "extra_add2"},
                        removed={"to_delete", "to_change", "to_change_surrounded",
                            "to_change==b||(c!=d&&e==f)", "a==b||(c!=to_change&&e==f)"}),
            TestCommit(
                TestFile("basic.c",
                    confident=TestAsserts(
                        added={"a", "to_delete", "c", "to_change", "d",
                            "to_change_surrounded", "f", "to_change==b||(c!=d&&e==f)",
                            "a==b||(c!=d&&e==no_change)", "a==b||(c!=to_change&&e==f)",
                            "good", "z", "x", "outside"}))),
        ]
        self.assert_matching_history()

    def assert_matching_history(self):
        """
        Assuming there are the same number of commits that affected
        assertions in the History as there are in self.expected, this
        checks that the given predicates match all assertions in the history
        for the given files at each points. It ignores files that are not
        included in a TestCommit.

        If a removed predicate contains "to_change". Then it verifies that there
        is an added "changed" assertion with same lineno.
        """
        self.assertEqual(len(self.expected), len(TestMineRepo.history.diffs))
        commits = zip(self.expected, TestMineRepo.history.diffs)j
        for expected_commit, actual_commit in commits:
            for file in expected_commit.files:
                self.assert_diff_file(diff, file)

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

    def assert_diff_file(self, diff, file):
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


        # A file's dict consists of three parts:

            # "confident": the good assertions that are in the .assertions field
            # "apologetic": the bad assertions that are regrettably undectabley
                # bad, so appear in .assertions field.
            # "problematic": the problematic assertions that are picked up.
        # There can be no whitespace in predicates.
class TestCommit():
    def __init__(self, *files):
        self.files = files

    @classmethod
    def from_diff(cls, diff):
        tc = cls(TestFile.from_file(f) for f in diff.files)
        return tc


class TestFile():
    def __init__(self, name,
            confident=TestAsserts(),
            problematic=TestAsserts(),
            apologetic=TestAsserts()):
        self.name = name
        self.confident = confident + apologetic
        self.problematic = problematic
        self.apologetic_count = apologetic.count()

    @classmethod
    def from_file(cls, file):
        confident=TestAsserts.from_assertions(file.assertions)
        problematic=TestAsserts.from_assertions(file.problematic)
        tf = cls(file.name, confident, problematic)
        return tf


class TestAsserts():
    def __init__(self, added=set(), removed=set()):
        self.added = added
        self.removed = removed

    @classmethod
    def from_assertions(cls, assertions):
        added = set()
        removed = set()
        for a in assertions:
            if a.change = Change.added:
                target = added
            elif a.change = Change.removed:
                target = removed
            else:
                raise Exception("Wrong assertion change: {c}".format(c=a.change))

            if a.problematic:
                target.add(remove_whitespace(" ".join(a.raw_lines)))
            else:
                target.add(remove_whitespace(a.predicate))

        # This is to guarantee that we don't accidentally create identical
        # asserts within one revision of a test file
        assert(len(assertions) == len(added) + len(removed))

        return cls(added, removed)

    def __add__(self, other):
        added = self.added.union(other.added)
        removed = self.removed.union(other.removed)
        return TestAsserts(added, removed)




def history_to_testcommits(history):
    return [TestCommit.from_diff(d) for d in history.diffs]





if __name__ == '__main__':
    unittest.main()
