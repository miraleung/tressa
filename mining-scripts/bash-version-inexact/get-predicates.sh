#!/bin/bash
# Get all distinct predicates, and print them to $TMPFILE

SRC=`pwd`/asserts
TMPFILE=`pwd`/bash-predicates_wip.txt
TMPFILE2=`pwd`/bash-predicates_wip2.txt
DSTFILE=`pwd`/bash-predicates.txt
PWD=`pwd`

TAB=$'\t'

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

for PATCH in $SRC/*.patch
do
  # Get all ASSERT exprs w/o prefixes, and those commented out too
  ASSERTS=`pcregrep -M '^[+-](\s*(//|/\*)?\s*)?ASSERT\s*\((\n*.*?\n*)*?\);' ${PATCH}`
  # If Xen syntax errors omitted ';', we add them back
#  ASSERTS="$(echo "$ASSERTS" | sed 's/)\s*$/);/g')"
  ASSERTS="$(echo "$ASSERTS" | sed 's/\\/\n/g')" # Remove line continuations (backslash)
  # Turn all tabs to spaces
  echo "$ASSERTS" > /tmp/temp_raw_asserts
  expand -t 4 /tmp/temp_raw_asserts > /tmp/tempfile
  ASSERTS=$(cat /tmp/tempfile)

	if [ -n "$ASSERTS" ]
  then
		while read ASSERT
		do
      IS_INT_DECL=`echo "$ASSERT" | grep '.*int\s*.*'`
      if [ -n "$IS_INT_DECL" ]
      then
        continue
      fi
			# Filter out "#define ASSERT()" statements
			NO_DEFINE=`echo "$ASSERT" | grep '.*#define.*'`
      ASSERT_BEGIN=`echo "$ASSERT" | grep '.*ASSERT('`
      ASSERT_END=`echo "$ASSERT" | grep '.*);.*'`

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

      if [ -z $HAS_ASSERT_BEGIN ] && [ -z $HAS_ASSERT_END ]
      then
        continue
      fi

			if [ -z "$NO_DEFINE" ]
			then
        FIRST_CHAR="${ASSERT_PRED:0:1}"
        IS_ADD=$((`[[ $FIRST_CHAR == '+' ]] && echo 1 || echo 0`))

        # Remove first +/-
        ASSERT_PRED="$(echo "$ASSERT" | sed 's/^[+-]//g')"

        # Remove lines of comments, empty lines,
        # backslashes, spaces, and BOL-comment markers for asserts.
        ASSERT_PRED="$(echo "$ASSERT_PRED" | \
          sed -r 's#^\s*(//|/\*|\\)?\s*$##; s/\s*//g; s#//##')"

        FILENAME=`basename ${PATCH#$PWD} .patch`
        # Assert is on one line
        if [ $HAS_ASSERT_BEGIN == 1 ] && [ $HAS_ASSERT_END == 1 ]
        then
          ASSERT_PRED="$(echo "$ASSERT_PRED" | sed -r 's#\s*(\*/|/\*.*\*/|//.*)?\s*$##;')"
          if ! grep -qe "$ASSERT_PRED" "$TMPFILE"
          then
            echo -e "Adding assert from $FILENAME:\n\t |$ASSERT_PRED|"
            echo "$ASSERT_PRED" >> $TMPFILE
          fi
        # Beginning of some line
        elif [ $HAS_ASSERT_BEGIN == 1 ] && [ $HAS_ASSERT_END == 0 ] && [ "$ASSERT_PRED" != "" ]
        then
          echo -e "\tAdding start of assert from $FILENAME:\n\t\t $ASSERT_PRED"
          echo "$ASSERT_PRED" >> $TMPFILE
        # On some middle line
        elif [ $HAS_ASSERT_BEGIN == 0 ] && [ $HAS_ASSERT_END == 0 ] && [ "$ASSERT_PRED" != "" ]
        then
          echo -e "\tAdding continuation from $FILENAME:\n\t\t $ASSERT_PRED"
          echo "$(cat $TMPFILE)$ASSERT_PRED" > $TMPFILE
        # On last line
        elif [ $HAS_ASSERT_BEGIN == 0 ] && [ $HAS_ASSERT_END == 1 ] && [ "$ASSERT_PRED" != "" ]
        then
          echo -e "\tAdding rest of predicate from $FILENAME:\n\t\t $ASSERT_PRED"
          echo "=== ASSERT_PRED IS |$ASSERT_PRED|"
          echo "$(cat $TMPFILE)$ASSERT_PRED" > $TMPFILE
        else
          echo -e "Empty line found: AP=|$ASSERT_PRED| (should be empty)"
        fi
			fi

		done <<< "$ASSERTS"

	fi
done


# Remove duplicate lines from file

for line in `awk '!a[$0]++' $TMPFILE`
do
  echo $line >> $TMPFILE2
done
awk '{$1=$1}1' $TMPFILE2 > $DSTFILE
yes | rm $TMPFILE
yes | rm $TMPFILE2
