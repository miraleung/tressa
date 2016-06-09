#!/bin/bash

# Prints to stdout the number of changed asserts in the ./asserts/ directory
# containing .patch files (as created by get-asserts.sh), grouped by addition +
# and removal -. (Ignores contextual asserts, as well as multiline asserts
# where the first line is unchanged)

SRC=asserts

if [ ! -d ${SRC} ]
then
	echo Directory ${SRC} doesn\'t exist, please run get-asserts.sh script first.
	exit 1
fi

cd ${SRC}

POS_TOTAL=0
NEG_TOTAL=0

for patch in *
do
	pos_count=`grep '^+.*ASSERT(' ${patch} | wc -l`
	neg_count=`grep '^-.*ASSERT(' ${patch} | wc -l`
	POS_TOTAL=$((POS_TOTAL+pos_count))
	NEG_TOTAL=$((NEG_TOTAL+neg_count))
done

echo Number of asserts added: ${POS_TOTAL}
echo Number of asserts removed: ${NEG_TOTAL}
