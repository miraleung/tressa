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
0.  Compile Haskell binaries:
    1.  `cd mining-scripts/haskell-version`
    2.  `ghc -O2 GetPredicates.hs -o GetPredicates`
    3.  `ghc -O2 GetActivity.hs -o GetActivity`
1. `DEST=/path/to/same/level/as/xen-unstable.hg`
2. `for f in mining-scripts/haskell-version/*.sh mining-scripts/haskell-version/*.hs; do cp $f $DEST/; done`
   1. Optional: Copy over Haskell binaries
      1. `for f in mining-scripts/haskell-version/GetPredicates mining-scripts/haskell-version/GetActivity; do cp $f $DEST; done`
3. `cp mining-scripts/cdf.py $DEST/`
4. `cd $DEST`
5. `./get-diffs.sh` (in `mining-scripts/`)
6. `./hs-getPredicates.sh`
7. `./hs-getActivity.sh`

##### hs-getPreds.sh
![Output of Haskell predicate getter](https://github.com/miraleung/tressa/raw/master/screenshots/hs-getpreds.png)

##### hs-getActivity.sh
![Output of Haskell revision-per-predicate (activity) miner](https://github.com/miraleung/tressa/raw/master/screenshots/hs-getactivity.png)


### Bash version (old and inexact)
#### Requirements
- Bash version 4.3.11(1)
- `sudo apt-get install pcregrep`

#### Usage
1. `DEST=/path/to/same/level/as/xen-unstable.hg`
2. `for f in mining-scripts/bash-version-inexact/*.sh; do cp $f $DEST/; done`
3. `for f in mining-scripts/bash-version-primitive/*.sh; do cp $f $DEST/; done`
4. `cp mining-scripts/cdf.py $DEST/`
5. `cd $DEST`
6. `./get-diffs.sh` (in `mining-scripts/`)
7. `./get-asserts.sh`
8. `./get-predicates.sh`
9. `./activity-preds.sh`

## Plot CDF
This measures the number of revisions affecting an assert, hence, its "activity" in the commit history.

1. `python cdf.py ${prefix}-activity-count.txt`
  - `prefix` is one of `hs` or `bash` for Haskell or Bash, respectively.

