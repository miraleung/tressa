## Script usage
### General requirements
- Mercurial
- Get [Xen](http://www.xenproject.org/) source
  - `hg clone http://xenbits.xensource.com/xen-unstable.hg`


### Haskell (new version, more exact)
#### Requirements
- **Version** 7.6.3
- **Dependencies** `cabal install regex-tdfa split`

#### Usage
1. `DEST=/path/to/same/level/as/xen-unstable.hg`
2. `for f in cdfscripts/*.sh cdfscripts.hs; do cp $f $DEST/; done`
   1. Optional: Copy over Haskell binaries
      1. `for f in cdfscripts/GetPreds cdfscripts/GetActivity; do cp $f $DEST; done`
3. `for f in scripts/*.sh; do cp $f $DEST/; done`
4. `cp cdf.py $DEST/`
5. `cd $DEST`
6. `./get-diffs.sh`
7. `./get-asserts.sh`
8. `./get-predicates.sh`
9. `./hs-getPredicates.sh`
10. `./hs-getActivity.sh`

### Bash version (old and inexact)
#### Requirements
- Bash version 4.3.11(1)
- `sudo apt-get install pcregrep`

#### Usage
1. `DEST=/path/to/same/level/as/xen-unstable.hg`
2. `for f in cdfscripts/bash-version/*.sh; do cp $f $DEST/; done`
3. `for f in scripts/*.sh; do cp $f $DEST/; done`
4. `cp cdf.py $DEST/`
5. `cd $DEST`
6. `./get-diffs.sh`
7. `./get-asserts.sh`
8. `./get-predicates.sh`
9. `./activity-preds.sh`

## Plot CDF
This measures the number of revisions affecting an assert, hence, its "activity" in the commit history.

1. `python cdf.py activity-count.txt`

