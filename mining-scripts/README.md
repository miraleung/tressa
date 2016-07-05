## Script usage

The main script under active development is the `python-version`. The Readme in its directory contains more specfic information about it.

The rest of the file is about the obsolecent `haskell-version`. Until recently, it was the main version.


#### Version summary:
Four script versions:
- `bash-version-primitive`: an early attempt to quickly mine ASSERTs
- `bash-version-inexact`: a strong attempt to provide ASSERT mining functionality, including preparing data for plotting. Ultimately, it still was inexact, and quite a bit hairy.
- `haskell-version`: Compiled Haskell programs as well as Bash wrapper scripts to more completely and effectively mine repos and source. **This used to be the best version to use**, although it is slow. The rest of this file explains this version.
- `python-version`: **This is the version under active development**. It is fast and represents a complete design departure from the others in that it respresents a project with an internal data structure. 


#### Additionally, useful:
- `hg-get-diffs.sh` for Mercurial, and `git-get-diffs.sh` for Git: extract diffs between all revisions into separate files.
- `python-version/cdf.py`: plots a Cummulative Distribution Function graph using `*-activity-count.txt` results from the other scripts.
- `install-haskell.sh`: an easy-setup script that compiles Haskell code and copies all necessary scripts to a target directory.

Mining Script Types:
- *Get Predicates*: extract a list of all Assertions in given code
- *Get Activity*: find how many revisions touch each assert. These scripts require a version-controlled repository and a directory of .patch files, as produced by `*-get-diffs.sh`

Most likely, you will want to use `hs-*.sh` scripts found in the *haskell-version/*, since the bash scripts are out of date. They rely on some compiled Haskell programs.



### Quick Start (for Ubuntu 14.04 and Haskell scripts)

### General requirements:
- **Haskell Version** 7.6.3
- **Haskell Dependencies** `regex-tdfa split`
- Python **scipy** library

#### Install dependencies
```
sudo apt-get install haskell-platform 
cabal update
cabal install regex-tdfa split
sudo apt-get install python-scipy
```

#### Run install script
Compiles the Haskell code and copies all necessary scripts to a target directory. This directory should be the repository (Git or Mercurial) that you want to mine.
```
./install-haskell.sh path/to/target/repo/dir/
```

#### Run scripts!
You may have to add executable permissions to some of the scripts with `chmod +xr <script>`.
If you are using a Git repo, then run `./git-get-diffs.sh asserts` instead.

```
cd path/to/target/repo/dir/
./hg-get-diffs.sh asserts   # Creates asserts/ directory
./hs-getPredicates.sh       # This takes many hours large repositories
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
4. `cp mining-scripts/python-version/cdf.py $DEST/`
5. `cd $DEST`
6. `./hg-get-diffs.sh` (in `mining-scripts/`)
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

