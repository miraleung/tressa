# Python 3.5

import subprocess
import re
import sys
import logging
from enum import Enum


################################################################################
# Constants
################################################################################


NUM_CONTEXT_LINES = 4
"""In diffs, this number of lines above or below the changed line"""

FILE_EXTENSIONS = "ch"
"""We only want to search .c or .h files"""




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
    """A container for relevant and questionable assertions in a given file."""
    # string -> File
    def __init__(self, name, assertions, inspects):
        self.name = name
        self.assertions = assertions
        self.to_inspect = inspects    # for difficult-to-parse asserts

    def __repr__(self):
        return "File('{n}')[{a}]".format(n=self.name, a=len(self.assertions))


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
    # string string string -> Diff
    def __init__(self, rvn_id, author, msg):
        self.rvn_id = rvn_id    # newer revision (commit) ID
        self.author = author
        self.msg = msg
        self.files = []     # Filenames of newest revision

    # string -> Diff
    def new(log_msg):
        """Produces a new Diff from a default git commit log entry, for
        example:

        commit b9f1de03869703000bf3016aa5697a09cfc55c0b
        Author: Graham St-Laurent <gstlaurent@gmail.com>
        Date:   Mon Jun 13 11:03:01 2016 -0700

            Created git-get-diffs.sh for Git, and added dir argument to both versions.

            Updated Readme and documentation comments to refer to new usage and
            names.

        """

        pattern = r"""commit\ (?P<commit>[0-9a-f]{40})\n
                      Author:\ (?P<author>.*?)\n
                      .*?\n\n
                      (?P<msg>.*)"""
        m = re.match(pattern, log_msg, re.VERBOSE | re.MULTILINE | re.DOTALL)

        if m is None:
            eprint("Improperly-formatted commit log")
            return Diff("", "", "")

        msg = p = re.sub("^    ", "", m.group("msg"), flags=re.MULTILINE)
        return Diff(m.group("commit"), m.group("author"), msg)

    def __str__(self):
        return "Diff: {id}".format(id=self.rvn_id)

    def __repr__(self):
        return "Diff('{id}', '{auth}', '{m}')[{files}]".format(
                id=self.rvn_id[:8], auth=self.author[:20], m=self.msg[:30],
                files=len(self.files))


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
    Broken = 3     # used for cases that require manual inspection


class Assertion():
    """The location and size within a file of an assertion expression. As well
    as its original parsed string, and a basic abstract syntax tree
    representation for performing basic analysis and comparison operations.
    """
    # int int string string Change -> Assertion
    def __init__(self, start_line, num_lines, raw_lines, assert_string, change=Change.NA):
        self.start_line = start_line
        self.num_lines = num_lines
        self.raw_lines = raw_lines          # original lines of code of assert
        self.change = change
        self.string = assert_string         # assertion expression as string
        self.ast = generateAST(raw_string)


# string -> Assertion
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
def mine_repo(repo_path, assertion_re, branch="master"):
    """Given the path to a Git repository and the name of any assertions used
    in this project, produces the History object containing all assertions
    that were added or removed between revisions, for the specified branch.
    """
    history = History()
    commits = getRevisionIds(repo_path, branch)
    for commit in commits:
        logging.info("Processing " + commit)
        patch = readPatch(repo_path, commit)
        diff = generate_diff(patch, assertion_re)
        if diff:
            history.diffs.append(diff) # diff won't exist if no assertions
    return history

    # history = History()
    # commits = getRevisionIds(repo_path, branch)
    # for commit in commits:
        # logging.info(Processing " + commit)
        # patch = readPatch(repo_path, commit)
        # log_msg, file_diffs = split_patch(patch)
        # files = generate_files(file_diffs, assertion_re)

        # if len(files) > 0:  # no need to create diff if if no assertions
            # diff = Diff.new(log_msg)
            # diff.files = files
            # history.diffs.append(diff)

    # return history

# string string -> Diff | None
def generate_diff(patch, assertion_re):
    """If there are any changed (or uncertain) assertions (matched by
    assertion_re) in a file in the given patch, produce Diff containing them.
    Otherwise produce None.
    """
    log_msg, file_diffs = split_patch(patch)
    files = generate_files(file_diffs, assertion_re)

    if len(files) == 0:
        return None

    diff = Diff.new(log_msg)
    diff.files = files
    return diff


# [string] string -> [File]
def generate_files(file_diffs, assertion_re):
    """Produce File for every changed-assertion-containing file_diff"""
    ext_pattern = r".*\.[{exts}]$".format(exts=FILE_EXTENSIONS)
    files = []
    for file_diff in file_diffs:
        filename = find_filename(file_diff)
        if re.match(ext_pattern, filename):
            # only care about files with appropriate extensions
            asserts, inspects = extract_assertions(file_diff, assertion_re)

            if len(assertions) + len(inspects) > 0:
                file = File(filename, assertions, inspects)
                files.append(file)


# string -> string
def find_filename(file_diff):
    """Finds name of "to" file in given diff, for example, this gives
    'newname.c' (it's okay if the initial 'diff' is missing):

    diff --git a/oldname.c b/newname.c
    index 91de014..c8dcc09 100644
    --- a/oldname.c
    +++ b/newname.c
    @@ -12 +12 @@ int somefun(int a) {
    -            a == 3 ||
    +            a == 4 ||
    """
    pattern = r"^\+\+\+ b/(?P<filename>.+?)$"
    m = re.search(pattern, file_diff, re.MULTILINE | re.DOTALL)

    if m is None:
        logging.error("Improperly-formatted diff string")
        return ""

    return m.group("filename")


# string string > [Assertion] [Assertion]
def extract_assertions(diff, assertion_re):
    """Produce list of Assertions generated for each assertion that appears in
    the given file's diff, provided that if it has been changed in some way
    (e.g, newly-added, removed, predicate-changed). Ignores unchanged
    assertions.Assertions are detected by matching the 'asserts' regular
    expression. Any assertions that appear suspicious or cannot be parsed
    properly are returned in the second list (with change=Change.Uncertain)
    """

    sections = extract_sections(diff)



# string -> [DiffSection]
def extract_sections(file_diff):
    secs = re.split(r"^@@ \S+ \+(\d+).*\n", file_diff,
            flags=re.MULTILINE) # note, parens keeps the starting line-number

    diff_secs = []
    try:
        pairs = iter(secs[1:]) # remove header, leaving linenum-diff pairs
        while True:
            linenum = int(next(pairs))
            body = next(pairs)
            ds = DiffSection(linenum, body)
            diff_secs.append(ds)
    except StopIteration:
        return diff_secs
    except:
        logging.error("Malformed file diff: " + find_filename(file_diff))
        return []


class DiffSection():
    """The body of a diff, beetween @@ headers."""
    # int string -> DiffSection
    def __init__(self, line_num, body):
        self.linenum = line_num
        self.body = body

    def __repr__(self):
        m = re.search("(\w.*)", self.body, re.MULTILINE)
        b = m.group(0) if m else "???"
        return "DiffSection(linenum={n}, body='{b}'".format(n=self.linenum, b=b)

























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


# string -> string, [string]
def split_patch(patch):
    """Return the commit log message, followed by a list of the diffs for
    each file in the patch. For simplicity's sake, it also removes the word
    'diff' from the beginning of each diff.
    """
    files = re.split("^diff", patch, flags=re.MULTILINE)
    msg_pos = re.findall
    return files[0], files[1:]















# string -> string
def remove_comments(text):
    # copied from http://stackoverflow.com/a/241506
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " " # note: a space and not an empty string
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, text)






# string string -> string
def runCommand(cmd, cwd, shell=False, input=None):
    """Given command and current working directory for command,
    returns its stdout. Throw exception if non-zero exit code. Shell=true
    means command can be written as usual; otherwise each word must be separate
    in list.
    """
    proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, shell=shell,
            input=input, check=True, universal_newlines=True)
    return proc.stdout








test_log_msg = """commit b9f1de03869703000bf3016aa5697a09cfc55c0b
Author: Graham St-Laurent <gstlaurent@gmail.com>
Date:   Mon Jun 13 11:03:01 2016 -0700

    Created git-get-diffs.sh for Git, and added dir argument to both versions.

    Updated Readme and documentation comments to refer to new usage and
    names.

"""

test_log_entry = """commit 5ff371e9d87f468bf73acfafd65ba5a0d1b7bd4f
Author: Wei Liu <wei.liu2@citrix.com>
Date:   Fri May 27 17:16:36 2016 +0100

    This reverts commit 55dc7f61260f4becc6c5e52a8155a6b8741c03cc.
    
    The get_maintainer.pl script showed Jan as the maintainer so I pushed
    this patch. But in fact according to MAINTAINERS file, he's not.  Revert
    this patch and wait until a maintainer acks it.

diff --git a/tools/tests/mce-test/tools/xen-mceinj.c b/tools/tests/mce-test/tools/xen-mceinj.c
index 51abc8a..061ec7c 100644
--- a/tools/tests/mce-test/tools/xen-mceinj.c
+++ b/tools/tests/mce-test/tools/xen-mceinj.c
@@ -317,10 +317,7 @@ static int inject_mci_addr(xc_interface *xc_handle,
                            domid_t domid)
 {
     return add_msr_bank_intpose(xc_handle, cpu_nr,
-                                MC_MSRINJ_F_INTERPOSE |
-                                ((domid >= DOMID_FIRST_RESERVED &&
-                                  domid != DOMID_SELF) ?
-                                 0 : MC_MSRINJ_F_GPADDR),
+                                MC_MSRINJ_F_INTERPOSE | MC_MSRINJ_F_GPADDR,
                                 MCi_type_ADDR, bank, val, domid);
 }
 
diff --git a/xen/arch/x86/cpu/mcheck/mce.c b/xen/arch/x86/cpu/mcheck/mce.c
index 0244553..cc446eb 100644
--- a/xen/arch/x86/cpu/mcheck/mce.c
+++ b/xen/arch/x86/cpu/mcheck/mce.c
@@ -1427,7 +1427,6 @@ long do_mca(XEN_GUEST_HANDLE_PARAM(xen_mc_t) u_xen_mc)
 
         if ( mc_msrinject->mcinj_flags & MC_MSRINJ_F_GPADDR )
         {
-            domid_t domid;
             struct domain *d;
             struct mcinfo_msr *msr;
             unsigned int i;
@@ -1460,7 +1452,7 @@ long do_mca(XEN_GUEST_HANDLE_PARAM(xen_mc_t) u_xen_mc)
                     put_gfn(d, gfn);
                     put_domain(d);
                     return x86_mcerr("do_mca inject: bad gfn %#lx of domain %d",
-                                     -EINVAL, gfn, domid);
+                                     -EINVAL, gfn, mc_msrinject->mcinj_domid);
                 }
 
                 msr->value = pfn_to_paddr(mfn) | (gaddr & (PAGE_SIZE - 1));
"""


