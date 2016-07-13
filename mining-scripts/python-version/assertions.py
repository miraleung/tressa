# Python 3.4
# dependency pygit2
# pycparser

# to print out all assertions in given repo:
#   $ python3 assertions.py <assertion_re> <repo_path> <branch> [--source]
# Prints assertions to stdout, and log to stderr
# Two groups of assertions: Confirmed assertions, and Those that need
# manual inspection. The confirmed assertions are printed first, sans
# whitespace. The # lines of the other assertions, up to where it became
# problematic are printed afterwards, but all on one line, with all whitespace
# compressed to one line.

# There is also a --source flag (must appear last). When used, the printed
# info will include the source of each assertion. It could be could for
# line scripting.
# commit:<problematic> (if applicable):file:line_number:+ (or) -:ASSERT(...)
#
# Example, that stores assertions in xen.asserts and log in xen.log, enabling source flag.
#   $ python3 assertions.py "assert|ASSERT|BUG_ON" /home/graham/xen master --source > xen3.asserts 2> xen3.log
# (Xen takes approximately 3 minutes to complete on my Intel i7 desktop)
#
#
#


import re
import logging
import itertools
import traceback
import sys
from enum import Enum
from collections import namedtuple

import pygit2
import pycparser

import predast

logging.basicConfig(level=logging.DEBUG)

################################################################################
# Constants
################################################################################


MAX_LINES = 10
"""Asserts longer than this may be declared problematic."""

FILE_EXTENSIONS = "ch"
"""We only want to search .c or .h files"""

MORE = False
DONE = True


################################################################################
# Data Definitions
################################################################################


class Source():
    """Represents all the assertions in the source files of a given revision,
    organized into files.
    """
    # string -> Source
    def __init__(self, revision_id):
        self.revision_id = revision_id
        self.files = []


class File():
    """A container for relevant and questionable assertions in a given file.
    If :diff: is included, it is its parent Diff from a repository mining.
    """
    # string (Diff) -> File
    def __init__(self, name, parent_diff=None):
        self.name = name
        self.assertions = []    # [Assertion]
        self.to_inspect = []    # [Assertion] for difficult-to-parse asserts
        self.parent_diff = parent_diff

    def __repr__(self):
        return "File('{n}',<{a} asserts> <{i} inspects>)".format(n=self.name,
                a=len(self.assertions), i = len(self.to_inspect))


class History():
    """Represents the results of a repository-mining session. All the assertions
    found are grouped by diff and into their files.
    """
    def __init__(self):
        self.diffs = []

    def show(self):
        for a in assertion_iter(self, inspects=False):
            print(a.info())

        for a in assertion_iter(self, inspects=True):
            print(a.info())


class Diff():
    """The files that had assertion changes in between adjacent revisions, as
    well as the IDs of those revisions. Diff with at most ONE other commit.
    """
    # string string int string [File] -> Diff
    def __init__(self, rvn_id, author, time, msg):
        self.rvn_id = rvn_id    # newer revision (commit) ID
        self.prev_id = ""       # commit id of the parent of this commit
        self.author = author
        self.time = time
        self.msg = msg
        self.files = []     # using filenames of newest revision

    def __str__(self):
        return "Diff: {id}".format(id=self.rvn_id)

    def __repr__(self):
        return "Diff('{id}', '{auth}', '{m}', <{f} files>)".format(
                id=self.rvn_id[:8], auth=self.author[:20],
                m=self.msg[:30].strip(), f=len(self.files))


class Change(Enum):
    """If the assertion was found while repo-mining, then this indicates
    whether it was added or removed. If found while searching one
    revision alone, then its Change state is '
    Note, this does not indicate whether two assertions are related through
    a simple change of an argument between revisions. Determining that
    is for later analysis.
    """
    none = (' ', ' ')
    added = ('+', '-')
    removed = ('-', '+')
    def __init__(self, prefix, anti_prefix):
        self.prefix = prefix
        self.anti_prefix = anti_prefix


class Assertion():
    """The location and size within a file of an assertion expression. As well
    as its original parsed string, and a basic abstract syntax tree
    representation for performing basic analysis and comparison operations.
    If :parent_file: exists, it points back to the File this was found in.
    :hunk_lineno: is included to help detect changed assertions, since they
    will likely be nearby.
    """
    # int int int [string] string string Change -> Assertion
    def __init__(self, lineno, hunk_lineno, num_lines, raw_lines, name, predicate,
            change=Change.none, problematic=False, problem="", parent_file=None):
        self.lineno = lineno            # start line num in file where it exists 
        self.hunk_lineno = hunk_lineno  # index into Hunk where it was found
        self.num_lines = num_lines
        self.raw_lines = raw_lines          # original lines of code of assert
        self.name = name                    # assert function name
        self.predicate = reduce_whitespace(predicate) # just pred string
        self.change = change
        self.problematic = problematic      # True if needs manual inspection
        self.problem = problem              # If problematic, this is the reason
        self.parent_file = parent_file
        self.ast = None # pycparser.c_ast of predicate

    def __str__(self):
        return "{name}({pred})".format(name=self.name, pred=self.predicate)

    def info(self):
        if self.problematic:
            problem = "<!{p}!>".format(p=self.problem)
            predicate = [reduce_spaces(l) for l in self.raw_lines]
        else:
            problem = ""
            predicate = "{n}({p})".format(n=self.name, p=self.predicate)

        return "{commit}:{problem}:{file}:{lineno}:{c}:{pred}".format(
            commit=self.parent_file.parent_diff.rvn_id, problem=problem,
            file=self.parent_file.name, lineno=self.lineno, c=self.change.prefix,
            pred=predicate)



# string -> string
def remove_whitespace(string):
    return re.sub(r"\s", "", string)

def reduce_whitespace(string):
    return re.sub(r"\s+", " ", string)

def reduce_spaces(string):
    return re.sub(r"[ \t]+", " ", string)


################################################################################
# Repo mining
################################################################################

# string string string -> History
def mine_repo(assertion_re, repo_path, branch):
    """Given the path to a Git repository and the name of any assertions used
    in this project, produces the History object containing all assertions
    that were added or removed between revisions, for the specified branch.
    """

    history = History()
    repo = pygit2.Repository(repo_path)
    for commit in repo.walk(repo.lookup_branch(branch).target,
            pygit2.GIT_SORT_TIME):
        logging.info("Processing " + commit.hex)
        diff = generate_diff(commit, repo, assertion_re)
        if diff:
            history.diffs.append(diff) # diff won't exist if no assertions

    parser = pycparser.c_parser.CParser()
    for diff in history.diffs:
        for file in diff.files:
            a_list = []
            for a in file.assertions:
                try:
                    a.ast = predast.AST(a.predicate, parser)
                    a_list.append(a)
                except Exception as err:
                    logging.error("Unable to generate AST of ({pred}): {e}" \
                            .format(pred=a.predicate, e=err))

                    a.ast = None
                    a.problematic = True
                    a.problem = "Problem generating AST"
                    file.to_inspect.append(a)
            file.assertions = a_list

    return history


# source is supposed to print out source: commit, file, lineno
def print_all_assertions(assertion_re, repo_path, branch, source=False):
    logging.basicConfig(level=logging.DEBUG, filename="assertions.log")
    hist = mine_repo(assertion_re, repo_path, branch)
    if not source:
        print("\nWell-formed assertions:\n")
        for a in assertion_iter(hist, inspects=False):
            print(a)

        print("\nProblematic assertions requiring manual inspection:\n")
        for a in assertion_iter(hist, inspects=True):
            print([reduce_spaces(l) for l in a.raw_lines])
    else:
        hist.show()


# History Boolean -> iterator[Assertion]
def assertion_iter(history, inspects=False):
    for diff in history.diffs:
        for file in diff.files:
            list_of_asserts = file.to_inspect if inspects else file.assertions
            for a in list_of_asserts:
                yield a


# pygit2.Commit pygit2.Repository string -> tressa.Diff | None
def generate_diff(commit, repo, assertion_re):
    """If there are any changed (or uncertain) assertions (matched by
    assertion_re) in a file in the given Commit, produce Diff containing them.
    Otherwise produce None.
    """
    diff = Diff(commit.hex, commit.author.name, commit.commit_time,
            commit.message)
    parents = commit.parents
    if len(parents) == 0:
        gdiff = commit.tree.diff_to_tree(swap=True,
                context_lines=MAX_LINES - 1)
    elif len(parents) == 1:
        gdiff = repo.diff(parents[0], commit, context_lines=MAX_LINES -1)
        diff.prev_id = commit.parent_ids[0]
    else:
        # don't diff merges or else we'll 'double-dip' on the assertions
        return None

    files = analyze_diff(gdiff, assertion_re, diff)
    if len(files) == 0:
        return None

    diff.files = files
    return diff


# pygit2.Diff string tressa.Diff -> [Files]
def analyze_diff(gdiff, assertion_re, diff):
    """Include File in list if it contains changed assertions"""
    ext_pattern = r".*\.[{exts}]$".format(exts=FILE_EXTENSIONS)
    files = []
    for patch in gdiff:
        filename = patch.delta.new_file.path
        if re.match(ext_pattern, filename):
            # only care about files with appropriate extensions
            logging.info("\t" + filename)
            file = File(filename, diff)
            asserts, inspects = analyze_patch(patch, assertion_re, file)

            if len(asserts) + len(inspects) > 0:
                file.assertions = asserts
                file.to_inspect = inspects
                files.append(file)
                logging.info("\t\t{a} assertions, {i} to_inspect".format(
                        a=len(file.assertions), i=len(file.to_inspect)))

        else:
            logging.info("\tSkipping " +  filename)
    return files


# pygit2.Patch string File -> [Assertion] [Assertion]
def analyze_patch(patch, assertion_re, file):
    """Produce list of changed Assertions found in given patch. Assertions
    are identified by assertion_re.
    """
    asserts, inspects = [], []
    for hunk in patch.hunks:
        a, i = generate_assertions(hunk, assertion_re, file)
        asserts.extend(a)
        inspects.extend(i)
    return asserts, inspects

# pygit2.Hunk string File -> [Assertion] [Assertion]
def generate_assertions(hunk, assertion_re, file):
    assertions = locate_assertions(hunk, assertion_re, file)
    asserts, inspects = [], []
    for a in assertions:
        try:
            # if something happens while extracting an assertion, we just
            # want to skip it and keep going, so as to not lose previous results
            add = a.extract_changed_assertion(Change.added)
            if add is not None:
                if add.problematic:
                    inspects.append(add)
                else:
                    asserts.append(add)

            rem = a.extract_changed_assertion(Change.removed)
            if rem is not None:
                if rem.problematic:
                    inspects.append(rem)
                else:
                    asserts.append(rem)

        except:
            header = a.hunk.header[:-1] # remove header's terminating newline
            logging.error("\t\tProblem extracting '{a}' in {h}"
                    .format(a=a.match.group(), h=header))
            traceback.print_exc()


    return asserts, inspects


# pygit2.Hunk string File -> [HunkAssertion]
def locate_assertions(hunk, assertion_re, file):
    """Finds all locations in the given hunk where the given regex identifies
    an assertion.
    """
    hunk_ass = []
    for i, line in enumerate(hunk.lines):
        matches = match_assertions(assertion_re, line.content)
        if matches:
            for m in matches:
                ha = HunkAssertion(hunk, i, m, file)
                hunk_ass.append(ha)

    return hunk_ass

# string string -> iterable[Match]
def match_assertions(assertion_re, line):
    regex = r"\b({asserts})\b".format(asserts=assertion_re)
    return re.finditer(regex, line)


class HunkAssertion():
    """An Assertion statement within a Hunk (a section of a diff's patch)."""
    def __init__(self, hunk, line_index, match, file):
        self.hunk = hunk
        self.line_index = line_index    # index of line in Hunk
        self.match = match
        self.file = file

    # Change -> Assertion|None
    def extract_changed_assertion(self, change):
        """Finds the given assertion, assuming it is Added or Removed
        (determined by :change: input). If successful, return create
        Assertion and return it. If it did not change as specified return None.
        If it seems to have changed, but produced parsing difficulties,
        return Assertion with .problematic flag turned on.

        problematic:
            - contains string that contains actual newline
            - reaches end of hunk or +MAX_LINES without closing paren,
            but at least one line had been changed
            - reaches */ before closing paren (not preceded by /*)
            - starts with *
            - has any weird characters on first line
            - couldn't generate AST

         return None:
            - first line is anti-changed
            - no lines from open to close are appropriately Changed
            - ASSERT is within Ignorable Characters (see below):
            - reaches end of hunk without any changed lines
            - line begins with #include
            - first non-space character after ASSERT is not (
            - #define ASSERT

        Ignoreable Characters (for paren-counting):
            - // to end of line
            - /* to */
            - " to " (but keep in 'string' field of Assertion)



        """

        first_gline = self.hunk.lines[self.line_index]
        if (first_gline.origin == change.anti_prefix) or \
            first_gline.content.startswith("#include"):
            return None

        lineno = first_gline.new_lineno if change == Change.added \
            else first_gline.old_lineno

        changed = False            # has the assertion been changed so far?
        count = 0
        extracter = Extracter(change, self.match)
        for gline in self.hunk.lines[self.line_index:]:
            if gline.origin != change.anti_prefix:
                if gline.origin == change.prefix:
                    changed = True
                status = extracter.extract(gline.content)
                count += 1
                if status == DONE or count > MAX_LINES:
                    break

        if not extracter.valid or not changed:
            return None

        if status != DONE:
            extracter.problematic = True
            if not extracter.problem:
                extracter.problem = "Exceeded max lines"

        predicate = strip_parens(extracter.predicate) \
                    if not extracter.problematic else ""

        if not extracter.problematic and not valid_predicate(predicate):
            return None

        if extracter.starred:
            extracter.problematic = True
            extracter.problem = "'*': possibly mid-comment"

        assertion = Assertion(lineno, self.line_index, len(extracter.lines),
                extracter.lines, self.match.group(), predicate, change=change,
                problematic=extracter.problematic, problem=extracter.problem,
                parent_file=self.file)
        return assertion


# string -> Boolean
def valid_predicate(predicate):
    """Return False if predicate is empty or a definition"""
    if remove_whitespace(predicate) == "":
        # is empty
        return False
    if re.match(r"\s*\w+\s+\w+", predicate):
        # is declaration
        return False
    return True


# string -> string
def strip_parens(exp):
    """Removes enclosing () pair from an expression"""
    exp = exp.strip()
    if exp[0] != "(" or exp[-1] != ")":
        raise Exception("Predicate not enclosed by parentheses")
    return exp[1:-1]


class Extracter():
    delims = re.compile(r'(//|/\*|\*/|"|\(|\)|#)')
    #                      1  2   3   4 5  6  7

    comment_clue = re.compile(r"\s*\*[^/]")

    def __init__(self, change, match):
        self.change = change            # Change
        self.match = match              # re.Match
        self.lines = []                 # pygit lines visited so far
        self.parens = 0                 # num parens seen so far
        self.comment = False
        self.predicate = ""              # final string, without comments
        self.valid = True
        self.problematic = False
        self.problem = False
        self.starred = False        # if assertline begins with *

    # re.Match -> Boolean
    def encompassed_by(self, match):
        """Return True if the match starts after self's ASSERT statement.
        For use with matched delimeter's, such as for '"' or '*/'
        """
        return match.start() > self.match.start()


    # string -> DONE | MORE
    def extract(self, line):
        """Update extracter based on next-received line. Return DONE when done,
        otherwise MORE. Assumes already checked if this is a valid line.
        """
        self.lines.append(line)

        if len(self.lines) == 1: # first line
            assertion_re = self.match.re.pattern


            # '#define ASSERT' should be ignored
            define_re = r"[ \t]*#[ \t]*define[ \t]+({a})\b".format(
                    a=assertion_re)
            match = re.match(define_re, line)
            if match:
                self.valid = False
                return DONE

            if Extracter.comment_clue.match(line):
                # don't return yet, since it may be rejected by form
                self.starred = True

            pre_line = line[:self.match.start()]
            while len(pre_line) > 0:
                match = Extracter.delims.search(pre_line)
                if match:

                    if match.group() == '"':
                        m = re.search('"', pre_line[match.end():])
                        if m is None:
                            self.valid = False
                            return DONE
                        else:
                            pre_line = pre_line[match.end() + m.end():]

                    elif match.group() == '/*':
                        m = re.search('\*/', pre_line[match.end():])
                        if m is None:
                            self.valid = False
                            return DONE
                        else:
                            pre_line = pre_line[match.end() + m.end():]

                    elif match.group() == "//":
                        self.valid = False
                        return DONE

                    else:
                        # '('   ')'   '#"
                        pre_line = pre_line[match.end():]

                else:
                    pre_line = ""

            line = line[self.match.end():]

        # The macro line continuation backslash messes up the AST parser
        line = re.sub(r"\\\n", " ", line)

        if self.comment:
            # We need to find find closing '*/' before moving on
            m = re.search('\*/', line)
            if m:
                line = line[m.end():]
                self.comment = False
            else:
                return MORE

        if self.parens == 0:
            # looking for opening '('
            line = line.strip()
            if line == '':
                return MORE
            if not line.startswith("("):
                self.valid = False
                return DONE

        while len(line) > 0:
            match = Extracter.delims.search(line)
            if match is None:
                self.predicate += line
                return MORE

            if match.group() == '"':
                m = re.search('"', line[match.end():])
                if m:
                    self.predicate += line[:match.end() + m.end()]
                    line = line[match.end() + m.end():]
                    continue
                else:
                    self.problematic = True
                    self.problem = "String seems to exceed one line"
                    return DONE

            elif match.group() == '/*':
                self.predicate += line[:match.start()]
                m = re.search('\*/', line[match.end():])
                if m:
                    line = line[match.end() + m.end():]
                    continue
                else:
                    self.comment = True
                    return MORE

            elif match.group() == "//":
                self.predicate += line[:match.start()]
                return MORE

            elif match.group() == "(":
                self.parens += 1
                self.predicate += line[:match.end()]
                line = line[match.end():]
                continue

            elif match.group() == ")":
                self.parens -= 1
                self.predicate += line[:match.end()]
                line = line[match.end():]

                if self.parens == 0:
                    return DONE

            elif match.group() == "*/":
                self.problematic = True
                self.problem = "'*/': possibly mid-comment"
                return DONE

            elif match.group() == "#":
                self.problematic = True
                self.problem = "'#': includes pre-processor directive"
                self.predicate += line[:match.start()]
                line = line[match.end():]
                continue


        return MORE

if __name__ == '__main__':
    argv = sys.argv
    source = True if (len(argv) == 5 and argv[4] == "--source") else False
    if not source and len(argv) != 4:
        print("Usage: {py} <assertion_re> <repo_path> <branch> [--source]"
                .format(py=argv[0]))
        exit(-1)

    print_all_assertions(argv[1], argv[2], argv[3], source)



