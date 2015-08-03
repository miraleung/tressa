#!/bin/bash
# Number of revisions per predicate

PWD=`pwd`
SRC=$PWD/asserts
TMPFILE=$PWD/tmp-hs-activity.txt
DSTFILE=$PWD/hs-activity.txt
COUNTFILE=$PWD/hs-activity-count.txt
PREDSFILE=$PWD/hs-predicates.txt

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

LINECOUNT=0
TOTALLINECOUNT=`cat $PREDSFILE | wc -l`
TOTALFILECOUNT=`ls $SRC/*.patch | wc -l`
declare -A ASSERTMAP
for LINE in `grep ASSERT $PREDSFILE`
do
  REVISION_COUNT=0
  LINECOUNT=$((LINECOUNT+1))
  echo "$LINECOUNT/$TOTALLINECOUNT: $LINE"
  ASSERTMAP[$LINE]=0
done

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

