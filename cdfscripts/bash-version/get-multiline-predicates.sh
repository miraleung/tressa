#!/bin/bash
# Get all distinct predicates, and print them to $TMPFILE

PWD=`pwd`
SRC=$PWD/asserts
PREFIX="multiline"
TMPFILE=$PWD/"$PREFIX-predicates_wip.txt"
TMPFILE2=$PWD/"$PREFIX-predicates_wip2.txt"
DSTFILE=$PWD/"$PREFIX-predicates.txt"

TAB=$'\t'

CODE_SAME=-1
CODE_DEL=0
CODE_ADD=1

function getstmcode() {
  if [ -z $1 ]
  then
    echo "function getstmcode(): no arg provided"
    exit 1
  fi
  if [[ "$1" == '+' ]]
  then
    echo $CODE_ADD
  elif [[ "$1" == '-' ]]
  then
    echo $CODE_DEL
  else
    echo $CODE_SAME
  fi;
}


if [ ! -d "$SRC" ]
then
	echo "ERROR: Directory $SRC doesn't exist, please run get-diffs.sh script first."
	exit 1
fi

# Create the files
if [ -f "$DSTFILE" ]
then
  read -p "Are you sure you want to get all the multiline predicates from scratch? y/[n] > " -n 1 -r
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

ASSERT_BUILDER=""
ASSERT_HEAD_SIGN=$CODE_SAME
ASSERT_SIGNS_DONE=0
STM_SIGN=$CODE_SAME
for PATCH in $SRC/*.patch
do
  # Get all ASSERT exprs w/o prefixes, and those commented out too, and
  # eliminate those that are #define or non-pure ASSERT statements.
  # Also get all lines that end with right parens, for mid-assert predicate changes.
  ASSERTS=`pcregrep --buffer-size 256K -M \
    '^(((.*[^#].*[^_]ASSERT\s*\((\n*.*?\n*)*?)?\);)|[+-].*\);)$' \
    ${PATCH} | pcregrep --buffer-size 256K -v "@"`

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
      ASSERT_END=`echo "$ASSERT" | grep '.*;.*'`

      # Deal with multiline asserts
      FC_ASSERT=${ASSERT:0:1}
      if [ -z "$ASSERT_BEGIN" ]
      then
        HAS_ASSERT_BEGIN=0
        STM_SIGN=`getstmcode $FC_ASSERT`
      else  # Line begins with an ASSERT statement
        HAS_ASSERT_BEGIN=1
        ASSERT_HEAD_SIGN=`getstmcode $FC_ASSERT`
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

      if [[ $HAS_ASSERT_END == 1 ]] && [[ $ASSERT_BUILDER == "" ]]
      then
        continue
      fi

			if [ -z "$NO_DEFINE" ]
			then
        FIRST_CHAR="${ASSERT_PRED:0:1}"
        IS_ADD=$CODE_SAME
        if [[ $FIRST_CHAR == '+' ]]
        then
          IS_ADD=$CODE_ADD
        elif [[ $FIRST_CHAR == '-' ]]
        then
          IS_ADD=$CODE_DEL
        fi
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
          ASSERT_PRED="$(echo "$ASSERT_PRED" | sed -r 's#\s*(\*/|/\*.*\*/|//.*)?\s*$##')"
          if ! grep -qe "$ASSERT_PRED" "$TMPFILE"
          then
            echo -e "Adding assert from $FILENAME:\n\t |$ASSERT_PRED|"
            echo "$ASSERT_PRED" >> $TMPFILE
          fi
          ASSERT_BUILDER=""
        # Beginning of some line
        elif [ $HAS_ASSERT_BEGIN == 1 ] && [ $HAS_ASSERT_END == 0 ] && [ "$ASSERT_PRED" != "" ]
        then
          ASSERT_BUILDER=$ASSERT_PRED
        # On some middle line
        elif [ $HAS_ASSERT_BEGIN == 0 ] && [ $HAS_ASSERT_END == 0 ] && [ "$ASSERT_BUILDER" != "" ]
        then
          if [[ $ASSERT_HEAD_SIGN == $STM_SIGN ]]
          then
            ASSERT_BUILDER+=$ASSERT_PRED
          else
            echo "$(cat $TMPFILE)$ASSERT_PRED" > $TMPFILE
          fi
        # On last line
        elif [ $HAS_ASSERT_BEGIN == 0 ] && [ $HAS_ASSERT_END == 1 ] && [ "$ASSERT_PRED" != "" ]
        then
          if [[ $ASSERT_HEAD_SIGN == $STM_SIGN ]]
          then
            ASSERT_BUILDER+=$ASSERT_PRED
            echo "Adding  $ASSERT_BUILDER from $FILENAME"
            echo "$(cat $TMPFILE)$ASSERT_BUILDER" > $TMPFILE
            ASSERT_BUILDER=""
            ASSERT_SIGNS_DONE=0
          else
            echo "Adding $ASSERT_BUILDER$ASSERT_PRED from $FILENAME"
            echo -e "$(cat $TMPFILE)$ASSERT_BUILDER$ASSERT_PRED" > $TMPFILE
            ASSERT_SIGNS_DONE=$((ASSERT_SIGNS_DONE+1))
          fi
          if [[ $ASSERT_SIGNS_DONE == 2 ]]
          then
            ASSERT_BUILDER=""
            ASSERT_SIGNS_DONE=0
          fi
        else
          continue
        fi
			fi

		done <<< "$ASSERTS"

	fi
done

# Remove ';', insert newlines
sed 's/;$//' $TMPFILE > $TMPFILE2
sed 's/ASSERT/\nASSERT/g' $TMPFILE2 > $TMPFILE

yes | rm $TMPFILE2
# Remove duplicate lines from file
for line in `awk '!a[$0]++' $TMPFILE`
do
  echo $line >> $TMPFILE2
done
awk '{$1=$1}1' $TMPFILE2 > $DSTFILE
yes | rm $TMPFILE
yes | rm $TMPFILE2
