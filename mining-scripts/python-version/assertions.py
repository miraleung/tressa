# Python 3.4
# dependency pygit2

import re
import logging
import itertools
import pygit2
from enum import Enum
from collections import namedtuple


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
    """
    # int int [string] string Change -> Assertion
    def __init__(self, start_lineno, num_lines, raw_lines, name, assert_string,
            change=Change.none, problematic=False):
        self.start_lineno = start_lineno
        self.num_lines = num_lines
        self.raw_lines = raw_lines          # original lines of code of assert
        self.name = name                    # assert function name
        self.string = assert_string         # assertion expression as string
        self.change = change
        self.problematic = problematic      # true if needs manual inspection
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
    return historye


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
        try:
            # if something happens while extracting an assertion, we just
            # want to skip it and keep going, so as to not lose previous results
            add = a.extract_changed_assertion(Change.Added)
            if add is not None:
                if add.problematic:
                    inspects.append(add)
                else:
                    asserts.append(add)

            rem = a.extract_changed_assertion(Change.Removed)
            if rem is not None:
                if rem.problematic:
                    inspects.append(rem)
                else:
                    asserts.append(rem)
        except err:
            logging.error("Problem extracting '{a}' in {h}: {e}"
                    .format(a=a.match.group(), h=a.hunk.header, e=err))

    return asserts, inspects


# pygit2.Hunk string -> [HunkAssertion]
def locate_assertions(hunk, assertion_re):
    """Finds all locations in the given hunk where the given regex identifies
    an assertion.
    """
    regex = r"\b({asserts})\b".format(asserts=asserts_re)
    hunk_ass = []
    while i, line in enumerate(hunk.lines):
        matches = re.finditer(regex, line)
        if matches:
            for m in matches:
                ha = HunkAssertion(hunk, i, m)
                hunk_ass.append(ha)

    return hunk_ass


class HunkAssertion():
    """An Assertion statement within a Hunk (a section of a diff's patch)."""
    def __init__(self, hunk, line_index, match):
        self.hunk = hunk
        self.line_index = line_index
        self.match = match

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
            - ASSERT line preceded by #define (could be part of another macro)
                - actually, a # appearing anywhere, since precomp directives...
            - has any weird characters on first line

         return None:
            - first line is anti-changed
            - no lines from open to close are appropriately Changed
            - ASSERT is among Ignorable Characters:
            - reaches end of hunk without any changed lines

        Ignoreable Characters (for paren-counting):
            - // to end of line
            - /* to */
            - " to " (but keep in 'string' field of Assertion)

        """
        if self.hunk.lines[self.line_index].origin == change.anti_prefix:
            return None

        extracter = Extracter(change, self.match)
        for line in self.hunk.lines[self.line_index:]:
            if line.origin != change.anti_prefix:
                status = extracter.extract(line)
                count += 1
                if status == DONE or count > NUM_CONTEXT_LINES + 1
                    break

        if not extracter.valid or not extracter.changed:
            return None

        if done != DONE:
            extracter.problematic = True

        lineno = extracter.lines[0].new_lineno if change == Change.Added \
            else extracter.lines[0].old_lineno
        lines = [l.content for l in extracter.lines]

        assertion = Assertion(lineno, len(lines), lines, self.match.group(),
                extracter.assert_string, change=change,
                problematic=extracter.problematic)
        return assertion


class Extracter():
    delims = re.compile(r'(//|\*  |/\*|\*/|"|#|\(|\))')
    #                      1  2    3   4   5 6 7  8

    def __init__(self, change, match):
        self.change = change            # Change
        self.match = match              # re.Match
        self.lines = []                 # pygit lines visited so far
        self.parens = 0                 # num parens seen so far
        self.comment = False
        self.assert_string = ""              # final string, without comments
        self.valid = True
        self.problematic = False
        self.changed = False            # the assertion has been changed so far


    # pygit2.Line -> DONE | MORE
    def extract(self, gline):
        """Update extracter based on next-received line. Return DONE when done,
        otherwise MORE. Assumes already checked if this is a valid line.
        """
        self.lines.append(gline)
        line = gline.content

        if gline.origin == self.change.prefix:
            self.changed = True

        if len(self.lines) == 1: # first line
            delims = Extracter.delims.finditer(line[:self.match.start()])
            for match in delims:
                d = match.group()
                if d == "//":
                    self.valid = False
                    return DONE
                else:
                    self.problematic = True
                    return DONE

            self.assert_string = self.match.group()
            line = line[self.match.end():]

        if self.comment:
            # We need to find find closing '*/' before moving on
            m = re.search('\*/', line)
            if m:
                line = line[m.end():]
            else:
                return MORE

        while len(line) > 0:
            match = Extracter.delims.search(line)
            if match is None:
                self.assert_string += line
                return MORE

            if match.group() == '"':
                m = re.search('"', line[match.end():])
                if m:
                    self.assert_string += line[:m.end()]
                    line = line[m.end():]
                    continue
                else:
                    self.problematic = True
                    return DONE

            elif match.group() == '/*':
                self.assert_string += line[:match.start()]
                m = re.search('\*/', line[match.end():])
                if m:
                    line = line[m.end():]
                    continue
                else:
                    self.comment = True
                    return MORE

            elif match.group() == "//":
                self.assert_string += line[:match.start()]
                return MORE

            elif match.group() == "(":
                self.parens += 1
                self.assert_string += line[:match.end()]
                line = line[match.end():]
                continue

            elif match.group() == ")":
                self.parens -= 1
                self.assert_string += line[:match.end()]
                if self.parens == 0:
                    return DONE

            else:
                # '*  ' or '*/' or '#'
                self.problematic = True
                return DONE

        return MORE





            # Must check for Comment status first























                    if self.match.start() > d.start():
                        self.valid = False
                        return True

        return False



        




        i = delims.finditer(line.content)
        for i in 





        i = iter(line.content)
        while True:
            try:
                c = next(i)
                if c == 

            except StopIteration:
                break

        # check for problematic termination
















        return False







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


