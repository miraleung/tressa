Python3 scripts using internal Assertion and git repo History
data structures to represent data. This allows us to apply a variety of
analyses to the data, and augment them over time.
More complete instructions concerning how we have used them so far
for learning about assertion usage, as well as for some of our results,
can be found in our [Google Drive](https://drive.google.com/drive/folders/0B6JneEGhQl01NFJZbUVpOS1nOWs?usp=sharing).

## Dependencies
- Python 3.4
- [pygit2](http://www.pygit2.org/)
- [pycparser](https://github.com/eliben/pycparser)
- Git

## Instructions
`assertions.py` contains functions for mining a cloned Git repository for assertion events. An event is an addition, removal, or change of an assertion. The principle function is `mine_repo(assertion_re, repo_path, branch)`, which produces a `History` object, which contains a list of `Diff` objects pertaining to each commit, each of which contains a `File` object with two lists of `Assertion` objects representing assertion events within that File. (One list `.assertions` is for high-confidence assertions, and the other `.to_inspect` is for problematic assertions that require manual inspection). For example:

```
from assertions import *
history = mine_repo("assert|ASSERT|BUG_ON", "path/to/target/repo", "master")
```

Another function `print_all_assertion(assertion_re, repo_path, branch, source=False)` will calculate then print out a given repo's History textually as a list of high-confidence assertions followed by a list of problematic assertions. If `source=True`, then it also prints out the source of each assertion: the commit, file, event, and line number. This command can be accessed from the command line as follows:
```
$ python3 assertions.py <assertion_re> <repo_path> <branch> [--source]
```
This prints the assertions to *stdout* and a progress log to *stderr*, so here's an example that saves both (with the source flag as *true*, in separate files:
```
$ python3 assertions.py "assert|ASSERT|BUG_ON" /home/graham/xen master --source > xen.asserts 2> xen.log
```
(The above command takes approximately 3 minutes to complete on my Intel i7 machine.)


## Testing
Tests for this are located in the `test_assertions.py` file. Their target is
the `tressa_test_repo/` directory. This is a [git **submodule**](https://git-scm.com/book/en/v2/Git-Tools-Submodules). In order to
properly integrate it with your local git environment, simply run
```
git submodule init
git submodule update
```
Alternatively, while initially cloning the Tressa repository, clone with
the `--recursive` flag to automatically download the submodule.
```
git clone --recursive  https://github.com/TressaOrg/tressa.git 

```

Once `tressa_test_repo/` has been cloned, then tests can be run as follows:
```
python3 test_assertions.py
```
