import unittest
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

    def test_get_function_context(self):
        def test_header(header, funcname):
            self.assertEqual(get_function_context(header), funcname)


        # Successful examples:
        test_header("@@ -336,2 +383,2 @@ static void domain_suspend_common_guest_suspended(libxl__egc *egc,",
                "domain_suspend_common_guest_suspended")
        test_header("@@ -252 +252 @@ void xsave(struct vcpu *v, uint64_t mask)",
                "xsave")
        test_header("@@ -4132,17 +4131,0 @@ void cr3_dump_list(struct cr3_value_struct *head){",
                "cr3_dump_list")

        # Failed examples:
        test_header("@@ -27 +26,0 @@", "")
        test_header("@@ -67 +67 @@ endif", "")
        test_header("@@ -283,0 +284,5 @@ struct acpi_dbg2_device {", "")
        test_header("@@ -23,0 +24,2 @@ int fill_console_start_info(struct dom0_vga_console_info *);", "")
        test_header("@@ -53 +53 @@ struct __packed __attribute__((aligned (64))) xsave_struct", "")



class TestMineRepo(unittest.TestCase):
    TEST_REPO = "tressa_test_repo"

    confident_count = 0
    problematic_count = 0
    apologetic_count = 0

    @classmethod
    def setUpClass(cls):
        cls.history = mine_repo("assert", TestMineRepo.TEST_REPO, "master")
        cls.actual_history = [TestCommit.from_diff(d) for d in cls.history.diffs]
        cls.history.show()
        print()

    @classmethod
    def tearDownClass(cls):
        print("Totals:")
        print("{c} confident; {p} problematic; {a} apologetic".format(
            c=cls.confident_count, p=cls.problematic_count,
            a=cls.apologetic_count))
        print()

    def setUp(self):
        print(self.id())

    def tearDown(self):
        c,p,a = self.count_asserts()
        TestMineRepo.confident_count += c
        TestMineRepo.problematic_count += p
        TestMineRepo.apologetic_count += a

        print("{c} confident; {p} problematic; {a} apologetic".format(
            c=c, p=p, a=a))
        print()

    def count_asserts(self):
        conf = 0; prob = 0; apol = 0
        for c in self.expected_history:
            for f in c.files:
                conf += len(f.confident)
                prob += len(f.problematic)
                apol += len(f.apologetic)
        return conf, prob, apol

    ############################################################################
    # The assertion tests
    ############################################################################


    def test_comments(self):
        """Verify proper behaviour involving comments in code"""
        self.expected_history = [
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
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
        self.assertHistoryEqual()

    def test_filetypes(self):
        """Ensure that non-c files are ignored"""
        self.expected_history = [
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(
                TestFile("longone.abc"),
                TestFile("longone.c.ccc"))
        ]
        self.assertHistoryEqual()

    def test_basic(self):
        """Basic add/remove/change situations"""
        self.expected_history = [
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(
                TestFile("basic.c",
                    confident=TestAsserts(
                        added={"changed", "changed_surrounded",
                            "changed==b||(c!=d&&e==f)", "a==b||(c!=changed&&e==f)",
                            "extra_add1", "extra_add2"},
                        removed={"to_delete", "to_change", "to_change_surrounded",
                            "to_change==b||(c!=d&&e==f)", "a==b||(c!=to_change&&e==f)"}))),
            TestCommit(
                TestFile("basic.c",
                    confident=TestAsserts(
                        added={"a", "to_delete", "c", "to_change", "d",
                            "to_change_surrounded", "f", "to_change==b||(c!=d&&e==f)",
                            "a==b||(c!=d&&e==no_change)", "a==b||(c!=to_change&&e==f)",
                            "good", "z", "x", "outside"}))),
        ]
        self.assertHistoryEqual()

    def test_macros(self):
        """Assertions within macros and including pre-processor directives"""
        self.expected_history = [
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(
                TestFile("macros.c",
                    confident=TestAsserts(
                        added={"(X)==1",
                            "(fun(_a)->field&SOME_mask)==SOME_shadow||(fun(_b)->field&ANOTHER_mask)==ANOTHER_shadow",
                            "*argv"}),
                    problematic=TestAsserts(
                        added={"prefix##_##name==0",
                            "a==1&&#ifdefFLAGarg==2#elsearg=3#endif&&b==2"}))),
            TestCommit(),
            TestCommit(),
        ]
        self.assertHistoryEqual()

    def test_strings(self):
        """Tests for assertions containing strings, or within strings"""
        self.expected_history = [
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(
                TestFile("strings.c",
                    confident=TestAsserts(
                        added={"\"string\"", "strcmp(\"singleline\",a)==0",
                            "strcmp(\"assert(a==b)\",a)==0",
                            "\"assert(c==d)\"!=NULL", "good==1"}),
                    problematic=TestAsserts(
                        added={"strncmp(\"multiline1", "strncmp(\"multiline2"}),
                    apologetic=TestAsserts(
                        added={"bad==0"}))),
            TestCommit(),
            TestCommit(),
            TestCommit(),
        ]
        self.assertHistoryEqual()

    def test_definitions(self):
        """Testing macro and function declarations, definitions, and prototypes"""
        self.expected_history = [
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(
                TestFile("definitions.c",
                    problematic=TestAsserts(
                        added={"int"}),
                    apologetic=TestAsserts(
                        added={"predicate"}))),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),

        ]
        self.assertHistoryEqual()

    def test_lines(self):
        """Testing multiple asserts per line, and asserts of to many lines"""
        self.expected_history = [
            TestCommit(),
            TestCommit(),
            TestCommit(
                TestFile("lines.c",
                    confident=TestAsserts(
                        added={"changed==1", "changed==2", "changed==3",
                            "changed==4", "changed==5", "to_add1",
                            "changed==6", "to_add2", "changed==7",
                            "to_add2", "to_add3"},
                        removed={"to_change==1", "to_change==2", "to_change==3",
                            "to_change==4", "to_delete1", "to_delete2",
                            "to_delete3", "to_change==5", "to_change==6",
                            "to_change==7"}),
                    apologetic=TestAsserts(
                        added={"no_change3", "no_change4", "no_change5",
                            "no_change6", "no_change7", "no_change8"},
                        removed={"no_change3", "no_change4", "no_change5",
                            "no_change6", "no_change7", "no_change8"}))),
            TestCommit(
                TestFile("lines.c",
                    confident=TestAsserts(
                        added={"good==1",
                            "no_change1", "no_change2", "to_change==1",
                            "to_change==2", "no_change3", "to_change==3",
                            "to_change==4", "no_change4",

                            "no_change5", "to_delete1", "to_delete2",
                            "no_change6",  "to_delete3", "to_change==5",

                            "to_change==6", "no_change7", "to_change==7",
                            "no_change8",

                            "a", "b", "c", "d", "e", "f", "g"}),
                    problematic=TestAsserts(added={"too_many_lines"}))),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),

        ]
        self.assertHistoryEqual()

    def test_mismatched(self):
        """Too many or too few parentheses"""
        self.expected_history = [
            TestCommit(),
            TestCommit(
                TestFile("mismatched.c",
                    problematic=TestAsserts(
                        added={"(a==1)||(b==2)", "too_few==1"}),
                    apologetic=TestAsserts( # it looks legitimate
                        added={"(c==3)&&(d==4)"}))),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
        ]
        self.assertHistoryEqual()

    def test_predicates(self):
        """Different types of easy and tricky predicates"""
        self.expected_history = [
            TestCommit(
                TestFile("predicates.c",
                    confident=TestAsserts(
                        added={"0", "variable",
                            "(((page->flags&PG_type_mask)==PGT_writeable_page)&&(page_type_count(page)!=0))||(((page->flags&PG_type_mask)==PGT_none)&&(page_type_count(page)==0))",
                            "*a==*((bob_t*)b)", "(*((int*)a))==3", "*a==(bob_t)3",
                            "offsetof(structS,f)==4",
                            "offsetof(structure,field)==0",
                            "sizeof(typename)==4"}),
                    problematic=TestAsserts(
                        added={"(int)a==((bob_t)b)",
                            "offsetof(structure,field1.field2)" }))),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
            TestCommit(),
        ]
        self.assertHistoryEqual()

    ############################################################################
    # Helper methods
    ############################################################################

    def assertHistoryEqual(self):
        """
        Assuming there are the same number of commits that affected
        assertions in the History as there are in self.expected, this
        checks that the given predicates match all assertions in the history
        for the given files at each points. It ignores files that are not
        included in a TestCommit.

        If a removed predicate contains "to_change". Then it verifies that there
        is an added corresponding "changed" assertion.
        """

        self.assertEqual(len(self.expected_history), len(TestMineRepo.actual_history))
        commits = zip(self.expected_history, TestMineRepo.actual_history)
        for expected_commit, actual_commit in commits:
            self.assertCommitEqual(expected_commit, actual_commit)

        self.assert_changes()

    def assert_changes(self):
        """This is to verify efficacy of the tests"""
        # TODO: move this to be related to a particular test-case, so no duplicates
        def find_changed(assertion, file):
            changed_pred = assertion.predicate.replace("to_change", "changed")
            for a in file.assertions:
                if a.predicate == changed_pred:
                    return a
            return None

        for a in assertion_iter(TestMineRepo.history, inspects=False):
            if a.change == Change.removed and "to_change" in a.predicate:
                changed_assertion = find_changed(a, a.parent_file)
                if not changed_assertion:
                    raise AssertionError("Expected 'changed' version of "
                        "assert({p}), but none found".format(p=a.predicate))

    def assertCommitEqual(self, expected_commit, actual_commit):
        def find_file(filename, files):
            for file in files:
                if filename == file.name:
                    return file
            # This isn't a bug in the test program, not tressa 
            raise LookupError("Expected file, but no actual: " + filename)

        # We ignore actual files that aren't expected. This lets us
        # organize the tests by file. However, we verify that empty files
        # are non-existant in actuality.

        for exp_file in expected_commit.files:

            if exp_file.empty():
                self.assertNotIn(exp_file.name, [f.name for f in actual_commit.files])
                continue

            act_file = find_file(exp_file.name, actual_commit.files)
            self.assertFileEqual(exp_file, act_file)

    def assertFileEqual(self, exp_file, act_file):
        # It's nice to have apologetics, but obviously Tressa can't distinguish
        # them, so we have to combine them with confidents to compare
        exp_confidents = exp_file.confident + exp_file.apologetic
        act_confidents = act_file.confident + act_file.apologetic
        self.assertAssertsEqual(exp_confidents, act_confidents)
        self.assertProblematicAssertsEqual(
                exp_file.problematic, act_file.problematic)

    def assertAssertsEqual(self, exp_asserts, act_asserts):
        self.assertSetEqual(exp_asserts.added, act_asserts.added)
        self.assertSetEqual(exp_asserts.removed, act_asserts.removed)

    def assertProblematicAssertsEqual(self, exp_asserts, act_asserts):
        self.assertAssertsMatch(exp_asserts.added, act_asserts.added)
        self.assertAssertsMatch(exp_asserts.removed, act_asserts.removed)

    def assertAssertsMatch(self, exp_assert_set, act_assert_set):
        # TODO: This is brittle; requires enough of the assert to have been added
        # to predicate fragment

        def find_match(predicate, strings):
            for string in strings:
                if predicate in string:
                    return string
            return None

        self.assertEqual(len(exp_assert_set), len(act_assert_set))
        act_assert_set = act_assert_set.copy()
        for a in exp_assert_set:
            act_assert = find_match(a, act_assert_set)
            if act_assert:
                act_assert_set.remove(act_assert)
            else:
                raise AssertionError("Problematic predicate not found: " + a)


################################################################################
# Test/Mock Classes
################################################################################

class TestAsserts():
    def __init__(self, added=set(), removed=set()):
        self.added = added
        self.removed = removed

    def __len__(self):
        return len(self.added) + len(self.removed)

    @classmethod
    def from_assertions(cls, assertions):
        """[Assertion] -> TestAsserts"""
        added = set()
        removed = set()
        for a in assertions:
            if a.change == Change.added:
                target = added
            elif a.change == Change.removed:
                target = removed
            else:
                raise Exception("Wrong assertion change: {c}".format(c=a.change))

            if a.problematic:
                target.add(remove_whitespace("".join(a.raw_lines)))
            else:
                target.add(remove_whitespace(a.predicate))

        ta = cls(added, removed)

        # This is to guarantee that we don't accidentally create identical
        # asserts within one revision of a test file
        # assert(len(assertions) == len(ta))

        return ta


    def __add__(self, other):
        added = self.added.union(other.added)
        removed = self.removed.union(other.removed)
        return TestAsserts(added, removed)


class TestFile():
    """The assertions found in a file. They are grouped into three categories:
        confident: the good assertions that are in the .assertions field
        apologetic: the bad assertions that are regrettably undectabley
                bad, so appear in .assertions field.
        problematic: the problematic assertions, from the .to_inspect field
    Not, there can be no whitespace in predicates here (any found
    predicates get their whitespace removed before being compared).
    """
    def __init__(self, name,
            confident=TestAsserts(),
            problematic=TestAsserts(),
            apologetic=TestAsserts()):
        self.name = name
        self.confident = confident + apologetic
        self.problematic = problematic
        self.apologetic = apologetic

    def empty(self):
        return len(self.confident) == 0 and \
               len(self.problematic) == 0 and \
               len(self.apologetic) == 0

    @classmethod
    def from_file(cls, file):
        confident=TestAsserts.from_assertions(file.assertions)
        problematic=TestAsserts.from_assertions(file.to_inspect)
        tf = cls(file.name, confident, problematic)
        return tf


class TestCommit():
    """A representation of a the assertions found in particular commit."""
    def __init__(self, *files):
        self.files = files

    @classmethod
    def from_diff(cls, diff):
        tc = cls()
        tc.files = [TestFile.from_file(f) for f in diff.files]
        return tc



if __name__ == '__main__':
    unittest.main()
