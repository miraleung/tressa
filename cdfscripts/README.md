## Usage
1. `DEST=/path/to/same/level/as/xen-unstable.hg`
2. `for f in cdfscripts/*.sh; do cp $f $DEST/; done`
3. `for f in scripts/*.sh; do cp $f $DEST/; done`
4. `cd $DEST`
5. `./get-diffs.sh`
6. `./get-asserts.sh`
7. `./get-predicates.sh`
8. The rest can be run in any order.
