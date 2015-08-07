# README
- `bash-version/bash-\*.txt` is the data file produced by running the Bash version of the data mining scripts
- `hs-\*.txt` is the one produced by the Haskell version - i.e. any `.sh` file prefixed by `hs-`
- `\*-activity-count.txt` is a list of the number of revisions in which a distinct predicate appears. This file is used for CDF graphing.
- `\*-activity.txt` maps the predicates and their respective counts, and is purely for informative purposes.
- `\*-predicates.txt` is a list of all the distinct predicates mentioned in all the revisions in Xen. This is used to build a map in the activity scripts.
- The revision of Xen on which data is gathered depends on that of the diffs gathered from get-diffs.sh. As of the time of writing, that is from  `xen-unstable.hg` at the changeset:
  ```
  changeset:   24450:50117a4d1a2c
  user:        Gang Wei <gang.wei@intel.com>
  date:        Mon Jan 02 12:43:07 2012 +0000
  summary:     x86/tboot: fix some coding style issues in tboot.c
  ```
