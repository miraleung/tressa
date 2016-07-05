# Copies all necessaray script-mining files to target repository directory
# (including both get-diffs.sh files).

E_BADARGS=85
if [[ $# -ne 1 ]]
then
    echo "Usage: $(basename $0) <target_repo>"
    exit $E_BADARGS
fi

REPO=$1

cp python-version/cdf.py git-get-diffs.sh hg-get-diffs.sh $REPO
cd ./haskell-version
ghc -O2 GetPredicates.hs -o GetPredicates
ghc -O2 GetActivity.hs -o GetActivity

printf "Copying scripts to ${REPO} ... "
cp GetActivity GetPredicates hs-getActivity.sh hs-getPredicates.sh $REPO
printf "Complete!\n"

















