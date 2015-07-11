#!/bin/bash
# Number of revisions per predicate

SRC=`pwd`/asserts
TMPFILE=`pwd`/ht-apreds.txt
DSTFILE=`pwd`/ht-activity.txt
COUNTFILE=`pwd`/ht-activity-count.txt
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

LINECOUNT=0
TOTALLINECOUNT=`cat predicates.txt | wc -l`
TOTALFILECOUNT=`ls $SRC/*.patch | wc -l`
declare -A ASSERTMAP
for LINE in `grep ASSERT predicates.txt`
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
  # Get all ASSERT exprs w/o prefixes, and those commented out too
  ASSERTS=`pcregrep --buffer-size 256K -M '^[+-]?\s*(//|/\*)?\s*ASSERT\s*\((\n*.*?\n*)*?\);' ${PATCH}`
#    ASSERTS="$(echo "$ASSERTS" | sed 's/)\s*$/);/g')"
  ASSERTS="$(echo "$ASSERTS" | sed 's/\\/\n/g')" # Remove line continuations (backslash)

  if [ -n "$ASSERTS" ]
  then
    while read ASSERT_0
    do
      PREFIX="xen-diff-"
      FILENUM=${FILENAME#$PREFIX}
      IS_INT_DECL=`echo "$ASSERT_0" | grep '.*int\s*.*'`
      if [ -n "$IS_INT_DECL" ]
      then
        ASSERT=""
        continue
      fi

      if [ -z "$ASSERT" ]
      then
#          echo -e "\tthis: $ASSERT\n\tthis2\t$ASESRT_0"
        ASSERT=$ASSERT_0
      fi
      # Filter out "#define ASSERT()" statements
      NO_DEFINE_0=`echo "$ASSERT_0" | grep '.*#define.*'`
      NO_DEFINE=`echo "$ASSERT" | grep '.*#define.*'`
      ASSERT_BEGIN=`echo "$ASSERT" | grep '.*ASSERT\s*('`
      ASSERT_END=`echo "$ASSERT" | grep '.*);.*'`
      ASSERT_0_BEGIN=`echo "$ASSERT_0" | grep '.*ASSERT\s*('`
      ASSERT_0_END=`echo "$ASSERT_0" | grep '.*)\s*;.*'`
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

#        echo -e "\t -- Doing $FILENAME: $ASSERT\n\t:: $ASSERT_O \n\t ::$ASSERTS"

      if [ -z "$NO_DEFINE_0" ] && [ -z "$NO_DEFINE" ]
      then
        ASSERT_PRED="$(echo "$ASSERT_0" | \
          sed -r 's#^[+-]##; s#^(	|\s)*(//|/\*|\\)?(	|\s)*$##; s/ //g')" # HAS HIDDEN TAB CHARS
        ASSERT_PRED="$(awk '{$1=$1}1' <<< $ASSERT_PRED)"
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
          if [ -n "$ASSERT" ] && [ ${ASSERTMAP[$ASSERT]+_} ];
          then
            NEWCOUNT=$((ASSERTMAP[$ASSERT] + 1))
            echo -e "\t$FILENAME ($FILECOUNT/$TOTALFILECOUNT): $NEWCOUNT::$ASSERT"
            ASSERTMAP["$ASSERT"]=$NEWCOUNT
          else
            echo -e "\t\tBad subscript: $ASSERT"
          fi
          ASSERT_WHOLE=0
        fi
      fi

    done <<< "$ASSERTS"
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

mv $TMPFILE $DSTFILE

