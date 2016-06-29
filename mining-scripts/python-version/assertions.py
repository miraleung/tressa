# Python 3.4
# dependency pygit2

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

import pygit2

from enum import Enum
from collections import namedtuple

logging.basicConfig(level=logging.DEBUG)

################################################################################
# Constants
################################################################################


NUM_CONTEXT_LINES = 4
"""In diffs, this number of lines above or below the changed line"""

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


class Diff():
    """The files that had assertion changes in between adjacent revisions, as
    well as the IDs of those revisions.
    """
    # string string int string [File] -> Diff
    def __init__(self, rvn_id, author, time, msg):
        self.rvn_id = rvn_id    # newer revision (commit) ID
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
    """
    # int int [string] string string Change -> Assertion
    def __init__(self, lineno, num_lines, raw_lines, name, predicate,
            change=Change.none, problematic=False, parent_file=None):
        self.lineno = lineno                # starting line num (in "to" file)
        self.num_lines = num_lines
        self.raw_lines = raw_lines          # original lines of code of assert
        self.name = name                    # assert function name
        self.predicate = reduce_whitespace(predicate)  # assertion expression
                                                   # as string minus whitespace
        self.change = change
        self.problematic = problematic      # true if needs manual inspection
        self.ast = self.generateAST()
        self.parent_file = parent_file

    def __str__(self):
        return "{name}({pred})".format(name=self.name, pred=self.predicate)

    # -> Assertion
    def generateAST(self):
        """Parses self.string to produce naive AST for basic analysis.
                AST = Abstract Syntax Tree
        """
        # TODO
        return None

# string -> string
def remove_whitespace(string):
    return re.sub(r"\s", "", string)

def reduce_whitespace(string):
    return re.sub(r"\s+", " ", string)



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
    return history


# source is supposed to print out source: commit, file, lineno
def print_all_assertions(assertion_re, repo_path, branch, source=False):
    logging.basicConfig(level=logging.DEBUG, filename="assertions.log")
    hist = mine_repo(assertion_re, repo_path, branch)
    if not source:
        print("\nWell-formed assertions:\n")
        for a in assertion_iter(hist, inspects=False):
            print(a)

        print("\nAssertions requiring manual inspection:\n")
        for a in assertion_iter(hist, inspects=True):
            raw = " ".join(a.raw_lines)
            print(reduce_whitespace(raw))
    else:
        for a in assertion_iter(hist, inspects=False):
            print("{commit}::{file}:{lineno}:{c}:{name}({predicate})".format(
                commit=a.parent_file.parent_diff.rvn_id,
                file=a.parent_file.name, lineno=a.lineno, c=a.change.prefix,
                name=a.name, predicate=a.predicate))

        for a in assertion_iter(hist, inspects=True):
            raw = " ".join(a.raw_lines)
            a_str = reduce_whitespace(raw)
            print("{commit}:<problematic>:{file}:{lineno}:{c}:{assertion}".format(
                commit=a.parent_file.parent_diff.rvn_id,
                file=a.parent_file.name, lineno=a.lineno, c=a.change.prefix,
                assertion=a_str))


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
                context_lines=NUM_CONTEXT_LINES)
    elif len(parents) == 1:
        gdiff = repo.diff(parents[0], commit, context_lines=NUM_CONTEXT_LINES)
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
        self.line_index = line_index
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
            - reaches end of hunk or +5 lines without closing paren,
            but at least one line had been changed
            - reaches */ before closing paren (not preceded by /*)
            - contains * followed by at least two spaces
            - has any weird characters on first line
            - has format of a declaration of the ASSERT

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
                if status == DONE or count > NUM_CONTEXT_LINES + 1:
                    break

        if not extracter.valid or not changed:
            return None

        if status != DONE:
            extracter.problematic = True

        predicate = strip_parens(extracter.predicate)
        assertion = Assertion(lineno, len(extracter.lines), extracter.lines,
                self.match.group(), predicate, change=change,
                problematic=extracter.problematic, parent_file=self.file)
        return assertion

# string -> string
def strip_parens(exp):
    """Removes enclosing () pair from an expression"""
    exp = exp.strip()
    if exp[0] != "(" or exp[-1] != ")":
        raise Exception("Predicate not enclosed by parentheses")
    return exp[1:-1]




class Extracter():
    delims = re.compile(r'(//|\*  |/\*|\*/|"|\(|\))')
    #                      1  2    3   4   5 6  7

    def __init__(self, change, match):
        self.change = change            # Change
        self.match = match              # re.Match
        self.lines = []                 # pygit lines visited so far
        self.parens = 0                 # num parens seen so far
        self.comment = False
        self.predicate = ""              # final string, without comments
        self.valid = True
        self.problematic = False

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

            # 'extern static unsigned long long ASSERT (X) {}' should be ignored
            # an ASSERT at the beginning of a line is probably in a declaration;
            # within a function, it would probably be indented
            decl_re = r"(((\w+ ){{0,4}}\w+ ({a}))|^({a}))\s*\(".format(a=assertion_re)
            match = re.match(decl_re, line)
            if match:
                self.problematic = True
                return DONE

            pre_line = line[:self.match.start()]
            while len(pre_line) > 0:
                match = Extracter.delims.search(pre_line)
                if match:

                    if match.group() == '"':
                        m = re.search('"', pre_line[match.end():])
                        if m is None:
                            self.valid = False
                            return DONE

                    elif match.group() == '/*':
                        m = re.search('\*/', pre_line[match.end():])
                        if m is None:
                            self.valid = False
                            return DONE

                    elif match.group() == "//":
                        self.valid = False
                        return DONE

                    elif match.group() == "*  ":
                        # might be mid-comment
                        self.problematic = True

                    # else: '*/'  '('   ')'
                    pre_line = pre_line[match.end():]
                else:
                    pre_line = ""

            line = line[self.match.end():]

        if self.comment:
            # We need to find find closing '*/' before moving on
            m = re.search('\*/', line)
            if m:
                line = line[m.end():]
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
                    self.predicate += line[:m.end()]
                    line = line[m.end():]
                    continue
                else:
                    self.problematic = True
                    return DONE

            elif match.group() == '/*':
                self.predicate += line[:match.start()]
                m = re.search('\*/', line[match.end():])
                if m:
                    line = line[m.end():]
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

            else:
                # '*  ' or '*/' 
                self.problematic = True
                return DONE

        return MORE

if __name__ == '__main__':
    argv = sys.argv
    source = True if (len(argv) == 5 and argv[4] == "--source") else False
    if not source and len(argv) != 4:
        print("Usage: {py} <assertion_re> <repo_path> <branch> [--source]"
                .format(py=argv[0]))
        exit(-1)

    print_all_assertions(argv[1], argv[2], argv[3], source)


