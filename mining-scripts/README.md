## Script usage

Three script versions, all created with Xen assertions in mind, but easily-adaptable:
- `bash-version-primitive`: an early attempt to quickly mine ASSERTs
- `bash-version-inexact`: a strong attempt to provide ASSERT mining functionality, including preparing data for plotting. Ultimately, it still was inexact, and quite a bit hairy.
- `haskell-version`: Compiled Haskell programs as well as Bash wrapper scripts to more completely and effectively mine repos and source.

Additionally, there is the Bash `get-diffs.sh` script, useful for Mercurial repositories, like Xen used to be, and the Python `cdf.py` script for plotting a graph with the `*-activity-count.txt` results from the other scripts.

Script-specific details can be found in their relevant directories.

### Quick Start (for Ubuntu 14.04 and Haskell scripts)

### General requirements for Xen example:
- Mercurial
- Get [Xen](http://www.xenproject.org/) source
  - `hg clone http://xenbits.xensource.com/xen-unstable.hg`
- **Haskell Version** 7.6.3
- **Haskell Dependencies** `regex-tdfa split`

#### Install dependencies
```
sudo apt-get install haskell-platform 
cabal update
cabal install regex-tdfa split
sudo apt-get install scipy
```

#### Compile Haskell Scripts
```
cd mining-scripts/haskell-version
ghc -O2 GetPredicates.hs -o GetPredicates
ghc -O2 GetActivity.hs -o GetActivity
cd ../..    # (back to top level of this repository)
```

#### Copy all scripts to repo to be mined
Currently, there is no way of specifying target directories in the scripts; so they must be physically present in the repo for them to work.

```
DEST=/path/to/repo/being/mined/e.g./xen-unstable.hg
cd mining-scripts
cp cdf.py get-diffs.sh $DEST
cd haskell-version
cp GetActivity GetPredicates hs-getActivity.sh hs-getPredicates.sh $DEST
cd ../..
```

#### Run scripts!
You may have to add executable permissions to some of the scripts with `chmod +xr <script>`.

```
cd $DEST
./get-diffs.sh      # (Creates $DEST/diffs/ directory; assumes Mercurial repo)
mv diffs asserts    # (The scripts require the directory be named 'asserts/')
./hs-getPredicates.sh    # (This takes many hours on Xen (but the older Bash scripts took seconds.)
./hs-getActivity.sh
./cdf.py hs-activity-count.txt
```
#### Example outputs

##### hs-getPreds.sh
![Output of Haskell predicate getter](https://github.com/miraleung/tressa/raw/master/screenshots/hs-getpreds.png)

##### hs-getActivity.sh
![Output of Haskell revision-per-predicate (activity) miner](https://github.com/miraleung/tressa/raw/master/screenshots/hs-getactivity.png)



## Bash version (old and inexact)
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

#### Requirements
- Python 2.7.6
- `python-scipy`

1. `python cdf.py ${prefix}-activity-count.txt`
  - `prefix` is one of `hs` or `bash` for Haskell or Bash, respectively.

