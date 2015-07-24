## Usage
1. `DEST=/path/to/same/level/as/xen-unstable.hg`
2. `for f in cdfscripts/*.sh; do cp $f $DEST/; done`
3. `for f in scripts/*.sh; do cp $f $DEST/; done`
4. `cp cdf.py $DEST/`
5. `cd $DEST`
6. `./get-diffs.sh`
7. `./get-asserts.sh`
8. `./get-predicates.sh`
9. The rest can be run in any order.

## Plot CDF
This measures the number of revisions affecting an assert, hence, its "activity" in the commit history.
1. `./activity-preds.sh`
2. `python cdf.py activity-count.txt`
