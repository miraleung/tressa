## Usage
1. `DEST=/path/to/same/level/as/xen-unstable.hg`
2. `for f in scripts/*.sh; do cp $f $DEST/; done`
3. `cd $DEST`
4. `./get-diffs.sh`
5. `./get-asserts.sh`
6. The rest can be run in any order.
