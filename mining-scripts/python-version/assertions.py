# Python 3.4

from enum import Enum


# Data Definitions

class Source():
    """Represents all the assertions in the source files of a given revision,
    organized into files."""
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
    found are grouped by diff and into their files."""
    def __init__(self):
        self.diffs = []


class Diff():
    """The files that had assertion changes in between adjacent revisions, as
    well as the IDs of those revisions."""
    def __init__(self, from_id, to_id):
        self.from_id = from_id
        self.to_id = to_id
        self.files = []


class Change(Enum):
    """If the assertion was found while repo-mining, then this indicates
    whether it was added or removed. If found while searching one
    revision alone, then its Change state is Not Applicable (NA).
    Note, this does not indicate whether two assertions are related through
    a simple change of an argument between revisions. Determining that
    is for later analysis."""
    NA = 0
    Added = 1
    Removed = 2


class Assertion():
    """The location and size within a file of an assertion expression. As well
    as its original parsed string, and a basic abstract syntax tree
    representation for performing basic analysis and comparison operations."""
    def __init__(self, start_line, num_lines, raw_string, change=Change.NA):
        self.start_line = start_line
        self.num_lines = num_lines
        self.raw_string = raw_string
        self.change = change
        self.ast = generateAST(raw_string)


def generateAST(assertion_string):
    """Given an assertion expression, produces naive AST for basic analysis.
    (Should this be a method of Assertion? I don't think so.)
            AST = Abstract Syntax Tree
    TODO
    """
    return None

