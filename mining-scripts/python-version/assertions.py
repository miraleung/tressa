# Python 3.4
# dependency pygit2

import re
import logging
import itertools
import pygit2
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
    # string string string [File] -> Diff
    def __init__(self, rvn_id, author, msg, files):
        self.rvn_id = rvn_id    # newer revision (commit) ID
        self.author = author
        self.msg = msg
        self.files = files     # using filenames of newest revision

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
    Uncertain = 3     # used for cases that require manual inspection


class Assertion():
    """The location and size within a file of an assertion expression. As well
    as its original parsed string, and a basic abstract syntax tree
    representation for performing basic analysis and comparison operations.
    """
    # int int string string Change -> Assertion
    def __init__(self, start_line, num_lines, raw_lines, name, assert_string,
            change=Change.NA):
        self.start_line = start_line
        self.num_lines = num_lines
        self.raw_lines = raw_lines          # original lines of code of assert
        self.name = name                    # assert function name
        self.string = assert_string         # assertion expression as string
        self.change = change
        self.ast = self.generateAST()

    # -> Assertion
    def generateAST(self):
        """Parses self.string to produce naive AST for basic analysis.
                AST = Abstract Syntax Tree
        """
        # TODO
        return None

################################################################################
# Repo mining
################################################################################

# path regex string -> History
def mine_repo(repo_path, assertion_re, branch="master"):
    """Given the path to a Git repository and the name of any assertions used
    in this project, produces the History object containing all assertions
    that were added or removed between revisions, for the specified branch.
    """

    history = History()
    repo = pygit2.Repository(repo_path)
    for commit in walk(repo.lookup_branch(branch).target):
        logging.info("Processing " + commit.id)
        diff = generate_diff(commit, asserts_re)
        if diff:
            history.diffs.append(diff) # diff won't exist if no assertions
    return history


# pygit2.Commit string -> tressa.Diff | None
def generate_diff(commit, assertion_re):
    """If there are any changed (or uncertain) assertions (matched by
    assertion_re) in a file in the given Commit, produce Diff containing them.
    Otherwise produce None.
    """
    parents = commit.parents
    if len(parents) == 0:
        diff = commit.tree.diff_to_tree(swap=True,
                context_lines=NUM_CONTEXT_LINES)
    elif len(parents) == 1:
        diff = repo.diff(parents[0], commit, context_lines=NUM_CONTEXT_LINES)
    else:
        # don't diff merges or else we'll 'double-dip' on the assertions
        return None

    files = analyze_diff(diff, assertion_re)
    if len(files) == 0:
        return None

    return Diff(commit.hex, commit.author.name, commit.message, files)


# pygit2.Diff string -> [Files]
def analyze_diff(diff, assertion_re):
    """Include File in list if it contains changed assertions"""
    ext_pattern = r".*\.[{exts}]$".format(exts=FILE_EXTENSIONS)
    files = []
    for patch in diff:
        filename = patch.delta.new_file.path
        if re.match(ext_pattern, filename):
            # only care about files with appropriate extensions
            logging.info("\t" + filename)
            asserts, inspects = analyze_patch(patch, assertion_re)

            if len(asserts) + len(inspects) > 0:
                file = File(filename, asserts, inspects)
                files.append(file)
        else:
            logging.info("\tSkipping " +  filename)
    return files


# pygit2.Patch string -> [Assertion] [Assertion]
def analyze_patch(patch, assertion_re):
    """Produce list of changed Assertions found in given patch. Assertions
    are identified by assertion_re.
    """
    asserts, inspects = [], []
    for hunk in patch.hunks:
        a, i = find_assertions(hunk, assertion_re)
        asserts.extend(a)
        inspects.extend(i)
    return asserts, inspects

# pygit2.Hunk string -> [Assertion] [Assertion]
def generate_assertions(hunk, assertion_re):
    assertions = locate_assertions(hunk, assertion_re)
    asserts, inspects = [], []
    for a in assertions:
        add, rem, unc = a.extract_changed_assertion()
        if add is not None:
            asserts.append(add)
        if rem is not None:
            asserts.append(rem)
        if unc is not None:
            inspects.append(unc)

    return asserts, inspects


# pygit2.Hunk string -> [HunkAssertion]
def locate_assertions(hunk, assertion_re):
    """Finds all locations in the given hunk where the given regex identifies
    an assertion.
    """
    hunk_ass = []
    i = 0
    while i < len(hunk.lines):
        line = hunk.lines[i]
        regex = r"\b({asserts})\b".format(asserts=asserts_re)
        matches = re.finditer(regex, line)
        if matches:
            for m in matches:
                ha = HunkAssertion(hunk, i, m.start(), m.end(), m.group())
                hunk_ass.append(ha)
    return hunk_ass


class HunkAssertion():
    """An Assertion statement within a Hunk (a section of a diff's patch)."""
    def __init__(self, hunk, start_line_index, startpos, endpos, name):
        self.hunk = hunk
        self.start_line_index = start_line_index
        self.startpos = startpos
        self.endpos = endpos
        self.name = name

    # -> Assertion|None, Assertion|None, Assertion|None
    def extract_changed_assertion(self):
        """If this corresponds to what appears to be an actual Added,
        or Removed or both assertion, then create them and return. If it
        there is a problem parsing the assertion or it looks suspicious,
        return it as the third. Return None for any cases where
        an assertion wasn't found.
        """
        # TODO
        return None, None, None






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


