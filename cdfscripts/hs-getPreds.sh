#!/bin/bash

PWD=`pwd`
SRC=$PWD/testasserts
TMPFILE=$PWD/hs-predicates_wip.txt
TMPFILE2=$PWD/hs-predicates_wip2.txt
DSTFILE=$PWD/hs-predicates.txt

HS_EXEC=GetPreds
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
  yes | rm $DSTFILE
fi
if [ -f "$TMPFILE" ]
then
  yes | rm $TMPFILE
fi
touch $TMPFILE

if [ -f $HS_SRC ]
then
  echo "Compiling $HS_SRC to $HS_EXEC ..."
  ghc -O2 -o "$HS_EXEC" $HS_SRC
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
awk '{$1=$1}1' $TMPFILE2 > $DSTFILE
yes | rm $TMPFILE
yes | rm $TMPFILE2


