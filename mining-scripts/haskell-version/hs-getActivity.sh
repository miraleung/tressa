#!/bin/bash
# Given a file of predicates and a direcotry of .patch files where those
# predicates were found, it produces two files:
#   1) hs-activity.txt: All the distint assertsion from all the files
#   along with counts of the number of files they appear in
#   2) hs-activity-count.txt: Just the counts for the predicates
# Additionally, it prints intermediate steps along the way to stdout.

# A wrapper for GetActivity.hs, which it will compile if necessary

# 3 preconditions: 
#   1) GetActivity or GetActivity.hs must exist
#   2) ./asserts/ contains files *.patch that each represent one revision
#   3) ./hs-predicates.txt has already been created (by hs-getPredicates.sh)
#       (Unfortunately, this means that it has the same weaknesses of GetPredicates.hs
#   
# Bug: only handled ASSERTs, not asserts (don' tknow about BUG_ONs)
# As well, it suffers from the same problems as GetActivity.hs, so it isn't
# ideal for diff/patch files at this point, which is its WHOLE PURPOSE, so,
# should be fixed.


PWD=`pwd`
SRC=$PWD/asserts
TMPFILE=$PWD/tmp-hs-activity.txt
DSTFILE=$PWD/hs-activity.txt
COUNTFILE=$PWD/hs-activity-count.txt
PREDSFILE=$PWD/hs-predicates.txt

ASSERTFMT="(ASSERT|assert|BUG_ON)" 

HS_EXEC=GetActivity
HS_SRC=GetActivity.hs

if [ ! -d "$SRC" ]
then
	echo "ERROR: Directory $SRC doesn't exist, please run get-diffs.sh script first."
	exit 1
fi

# Clean/create the files
if [ -f "$DSTFILE" ]
then
  read -p "Are you sure you want to get all the predicate activity from scratch? y/[n] > " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]
  then
    exit 1
  fi
  # Don't remove original activity file until the very end.
fi
if [ -f "$COUNTFILE" ]
then
  yes | rm $COUNTFILE
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

# Enumerates the assertions in the PREDSFILE 
LINECOUNT=0
TOTALLINECOUNT=`cat $PREDSFILE | wc -l`
TOTALFILECOUNT=`ls $SRC/*.patch | wc -l`
declare -A ASSERTMAP
for LINE in `grep -E $ASSERTFMT $PREDSFILE`
do
  REVISION_COUNT=0
  LINECOUNT=$((LINECOUNT+1))
  echo "$LINECOUNT/$TOTALLINECOUNT: $LINE"
  ASSERTMAP[$LINE]=0
done

# For each *.patch file, print its name, the number of distinct asserts within,
# including their per-file count so far
for PATCH in $SRC/*.patch
do
  FILENAME=`basename ${PATCH#$PWD} .patch`
  FILECOUNT=$((FILECOUNT+1))
  echo "Processing $FILENAME ($FILECOUNT/$TOTALFILECOUNT)"
  FILE_ASSERTS_STR=`./$HS_EXEC $PATCH`
  FILE_ASSERTS_RA=(${FILE_ASSERTS_STR/\\n//})
  echo "${#FILE_ASSERTS_RA[@]} distinct asserts found"
  if [ -n $FILE_ASSERTS_RA ]
  then
    for ASSERT in "${FILE_ASSERTS_RA[@]}"
    do
      if [ -n "$ASSERT" ] &&  test ${ASSERTMAP["$ASSERT"]+isset}
      then
        NEWCOUNT=$((${ASSERTMAP["$ASSERT"]} + 1))
        echo -e "\t$NEWCOUNT :: $ASSERT"
        ASSERTMAP["$ASSERT"]=$NEWCOUNT
      else
        echo -e "\t$ASSERT not found in map"
      fi
    done
  fi # Patch has asserts
done # FILE



# Print the final counts-per-file for each found assert, and output to DSTFILE
echo -e "==== Revision count per assert ===="
for ENTRY in "${!ASSERTMAP[@]}"
do
  REVISION_COUNT=${ASSERTMAP[$ENTRY]}
  echo "$REVISION_COUNT::$ENTRY"
  echo -e "$REVISION_COUNT :: $ENTRY" >> $TMPFILE
  echo -e "$REVISION_COUNT" >> $COUNTFILE
done # LINE

yes | rm $DSTFILE
mv $TMPFILE $DSTFILE

