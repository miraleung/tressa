#!/bin/bash

# A wrapper for the Hasekell program GetPredicates. It will try to compile
# GetPredicates.hs if the binary isn't available. 

# This runs GetPredicates For every .patch file in ./asserts/ and gathers
# the results in hs-predicates.txt. Additionally, it prints to stdout each
# filename, assertsion, and assertion count as they are found. 

# Unforunately, this suffers from GetPredicates.hs's problems with diff files,
# so there are many problems with the output. 

# 2 Preconditions:
#   1) GetPredicates or GetPredicates.hs must be in same directory as this script
#   2) ./asserts/ must exist and contain *.patch files


PWD=`pwd`
SRC=$PWD/asserts
TMPFILE=$PWD/tmp-hs-predicates.txt
TMPFILE2=$PWD/tmp2-hs-predicates.txt
DSTFILE=$PWD/hs-predicates.txt

HS_EXEC=GetPredicates
HS_SRC=GetPredicates.hs

if [ ! -d "$SRC" ]
then
	echo "ERROR: Directory $SRC doesn't exist, please run get-diffs.sh script first."
	exit 1
fi

# Create the files
if [ -f "$DSTFILE" ]
then
  read -p "Are you sure you want to get all the predicates from scratch? y/[n] > " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]
  then
    exit 1
  fi
  # Don't remove original predicates file until the very end.
fi
if [ -f "$TMPFILE" ]
then
  yes | rm $TMPFILE
fi
touch $TMPFILE

if [ -f $HS_SRC ]
then
  if [ -f $HS_EXEC ]
  then
    read -p "Recompile $HS_EXEC from source? y/[n] > " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
      echo "Compiling $HS_SRC to $HS_EXEC ..."
      ghc -O2 -o "$HS_EXEC" $HS_SRC
    fi
  else
    echo "Compiling $HS_SRC to $HS_EXEC ..."
    ghc -O2 -o "$HS_EXEC" $HS_SRC
  fi
fi

if [ ! -f $HS_EXEC ]
then
  echo "$HS_EXEC not found!"
  exit 1
fi

TOTAL_NUM_FILES=`ls $SRC/*.patch | wc -l`
FILECOUNT=0

for f in $SRC/*.patch
do
  FILENAME=`basename ${f#$PWD} .patch`
  FILECOUNT=$((FILECOUNT+1))
  echo "Processing $FILENAME ($FILECOUNT/$TOTAL_NUM_FILES)"
  ./$HS_EXEC $f $TMPFILE
done

for line in `awk '!a[$0]++' $TMPFILE`
do
  echo $line >> $TMPFILE2
done
yes | rm $DSTFILE
awk '{$1=$1}1' $TMPFILE2 > $DSTFILE
yes | rm $TMPFILE
yes | rm $TMPFILE2


