#!/bin/bash
# Number of revisions per predicate

SRC=`pwd`/asserts
TMPFILE=`pwd`/apreds.txt
DSTFILE=`pwd`/activity.txt
COUNTFILE=`pwd`/activity-count.txt
PWD=`pwd`

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
  yes | rm $DSTFILE
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

echo "# Number of revisions per predicate (activity)" >> $COUNTFILE

for LINE in `grep ASSERT predicates.txt`
do
  REVISION_COUNT=0
  echo "Doing assert $LINE"
  echo "$LINE" >> $TMPFILE
  for PATCH in $SRC/*.patch
  do
    FILENAME=`basename ${PATCH#$PWD} .patch`
    MATCH_COUNT=0
#    echo -e "\tFile $FILENAME"
    # Get all ASSERT exprs w/o prefixes, and those commented out too
    ASSERTS=`pcregrep -M '^[+-]\s*(//|/\*)?\s*ASSERT\s*\((\n*.*?\n*)*?\);' ${PATCH}`
    if [ -n "$ASSERTS" ]
    then
      while read ASSERT_0
      do
        if [ -z "$ASSERT" ]
        then
          ASSERT=$ASSERT_0
        fi

        # Filter out "#define ASSERT()" statements
        NO_DEFINE=`echo "$ASSERT" | grep '.*#define.*'`
        ASSERT_BEGIN=`echo "$ASSERT" | grep '.*ASSERT('`
        ASSERT_END=`echo "$ASSERT" | grep '.*);.*'`
        ASSERT_0_BEGIN=`echo "$ASSERT_0" | grep '.*ASSERT('`
        ASSERT_0_END=`echo "$ASSERT_0" | grep '.*);.*'`
        ASSERT_WHOLE=0

        # Deal with multiline asserts
        if [ -z "$ASSERT_BEGIN" ]
        then
          HAS_ASSERT_BEGIN=0
        else
          HAS_ASSERT_BEGIN=1
        fi
        if [ -z "$ASSERT_END" ]
        then
          HAS_ASSERT_END=0
        else
          HAS_ASSERT_END=1
        fi

        if [ -z "$NO_DEFINE" ]
        then
          ASSERT_PRED="$(echo "$ASSERT_0" | \
            sed -r 's#^[+-]##; s#^\s*(//|/\*)?\s*##; s/ //g')"
          # Assert is on one line
          if [ $HAS_ASSERT_BEGIN == 1 ] && [ $HAS_ASSERT_END == 1 ] #\
#            && [ -n "$ASSERT_0_BEGIN" ] && [ -n "$ASSERT_0_END" ]
          then
            ASSERT_PRED="$(echo "$ASSERT_PRED" | sed -r 's#\s*(\*/|/\*.*\*/|//.*)?\s*$##')"
            ASSERT=$ASSERT_PRED
#            echo -e "\tFound in $FILENAME: $ASSERT"
            ASSERT_WHOLE=1
          # Beginning of some line
          elif [ $HAS_ASSERT_BEGIN == 1 ] && [ $HAS_ASSERT_END == 0 ] && [ "$ASSERT_PRED" != "" ]
          then
            if [ -n "$ASSERT_0_BEGIN" ]
            then
#              echo -e "\tStart of assert from $FILENAME:\n\t\t $ASSERT_PRED"
              ASSERT=`echo "$ASSERT_PRED"`
            # On some middle line
            elif [ -z "$ASSERT_0_BEGIN" ] && [ -z "$ASSERT_0_END" ]
            then
              # Append
#              echo -e "\t\tCont from $FILENAME:\n\t\t $ASSERT_PRED"
              ASSERT=`echo "$ASSERT$ASSERT_PRED"`
            # On last line
            elif  [ -z "$ASSERT_0_BEGIN" ] && [ -n "$ASSERT_0_END" ]
            then
#              echo -e "\t\tRest of predicate from $FILENAME:\n\t\t $ASSERT_PRED"
              ASSERT=`echo "$ASSERT$ASSERT_PRED"`
              ASSERT_WHOLE=1
            else
              echo -e "Empty line found: AP=|$ASSERT_PRED| (should be empty)"
            fi
          fi
          if [ $ASSERT_WHOLE -gt 0 ]
          then
            if [[ "$ASSERT" == "$LINE" ]]
            then
#              echo -e "\t\t$FILENAME matches: $ASSERT"
              MATCH_COUNT=$((MATCH_COUNT+1))
#              echo "$ASSERT" >> $TMPFILE
            fi
            ASSERT_WHOLE=0
          fi
        fi

      done <<< "$ASSERTS"
      if [ $MATCH_COUNT -gt 0 ]
      then
        echo -e "\t$FILENAME: $MATCH_COUNT matches"
        REVISION_COUNT=$((REVISION_COUNT+1))
      fi

    fi # Patch has asserts
  done # FILE
  echo -e "\t$REVISION_COUNT" >> $TMPFILE
  echo -e "$REVISION_COUNT" >> $COUNTFILE
done # LINE

mv $TMPFILE $DSTFILE
