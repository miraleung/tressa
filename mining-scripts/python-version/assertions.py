# Python 3.5

import subprocess
import re
from enum import Enum


################################################################################
# Constants
################################################################################


NUM_CONTEXT_LINES = 4
"""In diffs, this number of lines above or below the changed line"""




################################################################################
# Data Definitions
################################################################################


class Source():
    """Represents all the assertions in the source files of a given revision,
    organized into files.
    """
    def __init__(self, revision_id):
        self.revision_id = revision_id
        self.files = []


class File():
    """A container for relevant assertions in a given file"""
    def __init__(self, name):
        self.name = name
        self.assertions = []


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
    def __init__(self, from_id, to_id, to_author, to_msg):
        self.from_id = from_id
        self.to_id = to_id
        self.to_author = to_author
        self.to_msg = to_msg
        self.files = []     # Filenames of "to" revision


class Change(Enum):
    """If the assertion was found while repo-mining, then this indicates
    whether it was added or removed. If found while searching one
    revision alone, then its Change state is Not Applicable (NA).
    Note, this does not indicate whether two assertions are related through
    a simple change of an argument between revisions. Determining that
    is for later analysis.
    """
    NA = 0
    Added = 1
    Removed = 2


class Assertion():
    """The location and size within a file of an assertion expression. As well
    as its original parsed string, and a basic abstract syntax tree
    representation for performing basic analysis and comparison operations.
    """
    def __init__(self, start_line, num_lines, raw_lines, assert_string, change=Change.NA):
        self.start_line = start_line
        self.num_lines = num_lines
        self.raw_lines = raw_lines          # original lines of code of assert
        self.change = change
        self.string = assert_string         # assertion expression as string
        self.ast = generateAST(raw_string)


def generateAST(assertion_string):
    """Given an assertion expression, produces naive AST for basic analysis.
    (Should this be a method of Assertion? I don't think so.)
            AST = Abstract Syntax Tree
    """
    # TODO
    return None

################################################################################
# Repo mining
################################################################################

# mineAssertions: assertionRegex -> History
    # history = new history
    # commits = getrevs
    # for commit in commits:
            # diff = gitlog -p

            # files = separateFiles
            # for file in files:



# path regex string -> History
def mineAssertions(repo_path, assertion_re, branch="master"):
    """Given the path to a Git repository and the name of any assertions used
    in this project, produces the History object containing all assertions
    that were added or removed between revisions, for the specified branch.
    """

    history = History()
    commits = getRevisionIds(repo_path, branch)
    for commit in commits:
        patch = readPatch(repo_path, commit)
        diff = makeDiff(patch)
        file_diffs = separateFiles(patch)

        for file_diff in file_diffs:
            assertions = extractChangedAssertions(file_diff, assertion_re)
            if len(assertions) > 0:
                file = makeFile(file_diff)
                file.assertions.extend(assertions)
                diff.files.append(file)

        if len(diff.files) > 0:     # No need to keep diff if it is empty
            history.diffs.append(diff)


# regex string -> [string]
def getRevisionIds(repo_path, branch):
    """Produce list of all commit Ids in history of given branch"""
    commits = runCommand(["git", "rev-list", branch], cwd=repo_path)
    return commits.splitlines()


# string string -> string
def readPatch(repo_path, rvn_id):
    """Produce commit message and diff file between given revision and its
    parent
    """
    context_size = "-U{n}".format(n=NUM_CONTEXT_LINES)
    return runCommand(["git", "log", "-p", "-1", context_size, rvn_id],
            cwd=repo_path)


# string -> [string]
def separateFiles(patch):
    """Extract the diff for each file in the given patch. For simplicity's sake,
    it also removes the word 'diff' from the beginning of each diff
    """
    files = re.split("^diff", patch, flags=re.MULTILINE)
    return files[1:]    # first element commit message


# string regex -> [Assertion]
def extractChangedAssertions(diff, asserts):
    """Produce list of Assertions generated for each assertion that appears in
    the given file's diff, provided that if it has been changed in some way
    (e.g, newly-added, removed, predicate-changed). Ignores unchanged
    assertions.Assertions are detected by matching the 'asserts' regular
    expression.
    """

    # TODO
    return []















# string string -> string
def runCommand(cmd, cwd, shell=False):
    """Given command and current working directory for command,
    returns its stdout. Throw exception if non-zero exit code. Shell=true
    means command can be written as usual; otherwise each word must be separate
    in list.
    """
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, shell=shell,
            check=True, universal_newlines=True)
    return proc.stdout









